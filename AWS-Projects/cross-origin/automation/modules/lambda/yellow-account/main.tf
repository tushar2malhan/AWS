# Create the IAM role
resource "aws_iam_role" "iam_role_yellow" {
  name = var.iam_role_name

  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
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
  role       = aws_iam_role.iam_role_yellow.name
}


resource "aws_iam_role_policy_attachment" "iam_role_yellow_cloudwatch" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
  role       = aws_iam_role.iam_role_yellow.name
}

resource "aws_iam_policy" "custom_policy_kinesis" {
  name        = var.iam_policy_name_kinesis
  description = "Custom policy to allow put record to Kinesis stream"
  policy      = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["kinesis:PutRecord","s3:*"]
        "Resource": "arn:aws:kinesis:ca-central-1:${var.blue_account_id}:stream/Paysafe-upf-dataops-Emr_Kinesis_details_Stream"
      }
    ]
  })
}

resource "aws_iam_policy" "custom_policy_assume_role" {
  name        = var.iam_policy_name_asssume
  description = "Custom policy to allow assume role"
  policy      = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::${var.blue_account_id}:role/Paysafe-upf-dataops-access-for-yellow"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "iam_role_yellow_custom_kinesis" {
  policy_arn = aws_iam_policy.custom_policy_kinesis.arn
  role       = aws_iam_role.iam_role_yellow.name
}

resource "aws_iam_role_policy_attachment" "iam_role_yellow_custom_assume_role" {
  policy_arn = aws_iam_policy.custom_policy_assume_role.arn
  role       = aws_iam_role.iam_role_yellow.name
}

# Create the Lambda function
data "archive_file" "lambda_code" {
  type        = "zip"
  source_file = var.python_file
  output_path = var.output_path
  depends_on  = [aws_iam_role_policy_attachment.iam_role_yellow_cloudwatch, aws_iam_role_policy_attachment.iam_role_yellow_custom_kinesis, aws_iam_role_policy_attachment.iam_role_yellow_custom_assume_role]
}

resource "aws_lambda_function" "lambda_function" {
  function_name    = var.function_name
  role             = aws_iam_role.iam_role_yellow.arn
  runtime          = var.runtime
  handler          = var.handler
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  timeout          = var.lambda_timeout
  memory_size      = 128
  publish          = true
  depends_on       = [aws_iam_role_policy_attachment.iam_role_yellow_cloudwatch]

  # environment variables
  environment{
    variables = {
      kinesis_stream_name = "Paysafe-upf-dataops-Emr_Kinesis_details_Stream"
      role_name = "Paysafe-upf-dataops-access-for-yellow"
      blue_account_id = var.blue_account_id
      config_file_key_name = var.config_file_key
    }
  }

}

# event bridge rule for yellow acc
resource "aws_cloudwatch_event_rule" "event_rule" {
  name          = var.event_rule_name
  event_pattern = jsonencode({
    "source": ["aws.logs"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
      "eventName": ["CreateLogStream"],
      "requestParameters": {
        "logStreamName": [{ "prefix": "states"}]
      },
      "eventSource": ["logs.amazonaws.com"]
    }
  })
}

# target for the event bridge rule
resource "aws_cloudwatch_event_target" "lambda_target" {
  arn       = aws_lambda_function.lambda_function.arn
  rule      = aws_cloudwatch_event_rule.event_rule.name
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