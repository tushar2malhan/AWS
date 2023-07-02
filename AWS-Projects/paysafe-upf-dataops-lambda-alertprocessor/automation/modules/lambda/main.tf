# This is required to get the AWS region via ${data.aws_region.current}.
data "aws_region" "current" {
}


# Iam policy for lambda function
resource "aws_iam_policy" "cloudwatch_dynamic_policy" {
  name   = var.iam_policy_name
  description = " IAM policy for full access to cloudwatch and dynamodb "

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor0",
      "Effect": "Allow",
      "Action": [
        "logs:*",
        "dynamodb:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}




# IAM lambda role for lambda function
resource "aws_iam_role" "lambda_role" {
  name    = var.iam_role_name
  description       = "Role for lambda function"
  assume_role_policy = <<EOF
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Effect": "Allow",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
        }   ]   }
    EOF
}


# Attach  policy to the role
resource "aws_iam_role_policy_attachment" "cloudwatch_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.cloudwatch_dynamic_policy.arn
}


# archive lambda function
data "archive_file" "lambda_code" {
  type        = "zip"
  source_file = var.python_file
  output_path = var.output_path
  depends_on  = [aws_iam_role.lambda_role]
}

# Python lambda function
resource "aws_lambda_function" "lambda_function" {
  function_name    = var.function_name
  role             = aws_iam_role.lambda_role.arn
  runtime          = var.runtime
  handler          = var.handler
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256
  timeout          = var.lambda_timeout
  memory_size      = 128
  publish          = true
  depends_on       = [aws_iam_role.lambda_role]


}

# event bridge rule
resource "aws_cloudwatch_event_rule" "event_rule" {
  name          = var.event_rule_name
  event_pattern = <<EOF
{ 
  "source": ["aws.logs"], 
  "detail-type": ["AWS API Call via CloudTrail"], 
  "detail": { 
    "eventSource": ["logs.amazonaws.com"], 
    "eventName": ["CreateLogGroup", "CreateLogStream", "PutLogEvents"] 
  } 
}
EOF
}

# target for the event bridge rule
resource "aws_cloudwatch_event_target" "event_target" {
  arn  = aws_lambda_function.lambda_function.arn
  rule = aws_cloudwatch_event_rule.event_rule.name
}

# Lambda permissions
resource "aws_lambda_permission" "allow_cloudwatch_to_call_rw_fallout_retry_step_deletion_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.event_rule.arn
}

# dynamodb table provisioned
resource "aws_dynamodb_table" "alertDashboard_logs" {
  name           = var.dynamodb_name
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "event"
  attribute {
    name = "event"
    type = "S"
  }
}



