
# This is required to get the AWS region via ${data.aws_region.current}.
data "aws_region" "current" {
}



# IAM role for PUBLISHER LAMBDA - Trust policy 
resource "aws_iam_role" "filter_role" {
  name = "Paysafe-upf-dataops-Publisher-${var.account_id}-role"
   assume_role_policy = <<POLICY
{
  
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com",
                "AWS": "arn:aws:iam::${var.yellow_account_id}:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {}
        }
    ]
}
POLICY
}


resource "aws_iam_policy" "kinesis-logs-full-access-policy" {
  name        = "Paysafe-upf-dataops-kinesis-full-access-${var.account_id}"
  description = "Provides full access to Kinesis and Logs for the resource ARN arn:aws:kinesis:ca-central-1:${var.account_id}:stream/${var.kinesis_stream_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "kinesis:*",
          "logs:*"
        ]
        Resource = "arn:aws:kinesis:ca-central-1:${var.account_id}:stream/${var.kinesis_stream_name}"
      }
    ]
  })
}

# iam policy for s3 get object
resource "aws_iam_policy" "lambda-s3-get-object-access" {
  name        = "Paysafe-upf-dataops-lambda-s3-get-object-access-${var.account_id}"
  description = "Provides access to GetObject on specific S3 object for the Lambda function ARN ${aws_lambda_function.lambda_function.arn}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "arn:aws:s3:::paysafe-upf-dataops-properties/${var.config_file_key}"
      }
    ]
  })
}

# Attach Iam policy for s3 get object 
resource "aws_iam_role_policy_attachment" "publisher_lambda_s3_access" {
  policy_arn = aws_iam_policy.lambda-s3-get-object-access.arn
  role       = aws_iam_role.filter_role.name
}



#Attach policy to role for PUBLISHER lambda function
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment-2" {
  policy_arn = aws_iam_policy.kinesis-logs-full-access-policy.arn
  role = aws_iam_role.filter_role.name
}

#Attach policy to role for PUBLISHER lambda function
resource "aws_iam_role_policy_attachment" "cloudwatch-attachment" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
  role       = aws_iam_role.filter_role.name
  depends_on = [aws_lambda_function.lambda_function]
}

# archive lambda function blue acc - PUBLISHER
data "archive_file" "lambda_code" {
  type        = "zip"
  source_file = var.python_file
  output_path = var.output_path
  depends_on  = [aws_iam_role.filter_role]
}

# Python lambda function blue acc - PUBLISHER
resource "aws_lambda_function" "lambda_function" {
  function_name    = var.function_name
  role             = aws_iam_role.filter_role.arn
  runtime          = var.runtime
  handler          = var.handler
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  timeout          = var.lambda_timeout
  memory_size      = 128
  publish          = true
  depends_on       = [aws_iam_role.filter_role]

  # environment variables - PUBLISHER
  environment{
    variables = {
      kinesis_stream_name = var.kinesis_stream_name
      dynamodb_name = var.dynamodb_name
      grey_account_id = var.grey_account_id
      yellow_account_id = var.yellow_account_id
      config_file_key_name = var.config_file_key
    }
  }
}


# event bridge rule for blue acc
resource "aws_cloudwatch_event_rule" "event_rule" {
  name          = var.event_rule_name
  event_pattern = jsonencode({
  "source": ["aws.logs"], 
  "detail-type": ["AWS API Call via CloudTrail"], 
  "detail": { 
     "eventName": ["CreateLogStream"],
     "requestParameters": {"logStreamName": [{ "prefix": "states"}]},
    "eventSource": ["logs.amazonaws.com"],
  } 
})
}

# target for the event bridge rule
resource "aws_cloudwatch_event_target" "lambda_target" {
  arn  = aws_lambda_function.lambda_function.arn
  rule = aws_cloudwatch_event_rule.event_rule.name
  target_id = "lambda_target"
}

# Lambda permissions
resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.event_rule.arn
}

#Define Kinesis Stream
resource "aws_kinesis_stream" "emr_cluster_details_stream" {
  name = var.kinesis_stream_name
  shard_count = 1
  retention_period = 24
}

resource "aws_cloudwatch_log_group" "log_group" {
  name = "/aws/lambda/producer-lambda-function"  
}

# Create IAM Role for Lambda MAIN CONSUMER Function
resource "aws_iam_role" "consumer_role" {
  name = var.iam_role_main_consumer

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Create IAM Policy for Lambda  MAIN CONSUMER Function
resource "aws_iam_policy" "lambda_policy" {
  name        = var.iam_policy_main_consumer
  description = "Policy for Lambda function to access Kinesis, DynamoDB, and CloudWatch"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "dynamodb:PutItem",
          "dynamodb:Query"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:DescribeStream",
          "kinesis:ListShards",
          "kinesis:ListStreams"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach IAM Policy to IAM Role FOR MAIN CONSUMER
resource "aws_iam_role_policy_attachment" "consumer_role_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_policy.arn
  role       = aws_iam_role.consumer_role.name
}

# archive lambda function - MAIN CONSUMER
data "archive_file" "lambda_code2" {
  type        = "zip"
  source_file = var.main_consumer_python_file
  output_path = var.main_consumer_output_py 
  depends_on  = [aws_iam_role.consumer_role]
}

# Python lambda function - MAIN CONSUMER
resource "aws_lambda_function" "persists_to_dynamodb" {
  function_name    = var.main_consumer_function_name
  role             = aws_iam_role.consumer_role.arn
  runtime          = "python3.8"
  handler          = "persist_to_dynamodb_lambda.lambda_handler"
  filename         = data.archive_file.lambda_code2.output_path
  source_code_hash = data.archive_file.lambda_code2.output_base64sha256
  timeout          = 60
  memory_size      = 128
  publish          = true
  depends_on       = [aws_iam_role.consumer_role]

  
  # environment variables
  environment{
    variables = {
      kinesis_stream_name = var.kinesis_stream_name
      dynamodb_name = var.dynamodb_name
      grey_account_id = var.grey_account_id
      yellow_account_id = var.yellow_account_id
    }
  }
}


# Map Kinesis to MAIN CONSUMER Lambda Function
resource "aws_lambda_event_source_mapping" "kinesis_trigger" {
  event_source_arn =  aws_kinesis_stream.emr_cluster_details_stream.arn
  function_name = aws_lambda_function.persists_to_dynamodb.function_name
  starting_position = "LATEST"
}

#  Dynamo Db table
resource "aws_dynamodb_table" "emr_cluster_details_db" {
  name = var.dynamodb_name
  read_capacity  = 10
  write_capacity = 10
  hash_key = "id"
  range_key = "Zone"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "Zone"
    type = "S"
  }

}


# IAM role for yellow account
resource "aws_iam_role" "test_for_yellow_2" {
  name = var.iam_role_name_for_yellow

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.yellow_account_id}:root"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Allow iam policy to put record in kinesis data stream in blue account from yellow account
resource "aws_iam_policy" "test_policy_for_yellow" {
  name = "Kinesis-put-record-yellow-2"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "kinesis:PutRecord"
        Resource = "arn:aws:kinesis:ca-central-1:${var.account_id}:stream/${var.kinesis_stream_name}"
      }
    ]
  })
}

# Attached the above iam policy to iam role 
resource "aws_iam_role_policy_attachment" "test-for-yellow-attachment" {
  policy_arn = aws_iam_policy.test_policy_for_yellow.arn
  role       = aws_iam_role.test_for_yellow_2.name
}


# IAM role for Grey account
resource "aws_iam_role" "test_for_grey_2" {
  name = var.iam_role_name_for_grey

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.grey_account_id}:root"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Allow iam policy to put record in kinesis data stream in blue account from grey account
resource "aws_iam_policy" "test_policy_for_grey" {
  name = "Kinesis-put-record-grey-2"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "kinesis:PutRecord"
        Resource = "arn:aws:kinesis:ca-central-1:${var.account_id}:stream/${var.kinesis_stream_name}"
      }
    ]
  })
}

# Attach IAM policy to the IAM role in the grey account
resource "aws_iam_role_policy_attachment" "test-for-grey-attachment" {
  policy_arn = aws_iam_policy.test_policy_for_grey.arn
  role       = aws_iam_role.test_for_grey_2.name
}
