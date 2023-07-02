data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "policy_doc" {
  statement {
    actions   = ["s3:*"]
    resources = ["arn:aws:s3:::*"]
    effect = "Allow"
  }
  statement {
    actions = ["events:*"]
    resources = ["*"]
    effect  =  "Allow"
  }
  statement {
    actions   = ["kinesis:*"]
    resources = ["*"]
    effect = "Allow"
  }
  statement {
    actions   = ["dynamodb:*"]
    resources = ["arn:aws:dynamodb:::*"]
    effect = "Allow"
  }
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = ["arn:aws:secretsmanager:::*"]
    effect = "Allow"
  }
  statement {
    actions   = ["logs:CreateLogStream","logs:PutLogEvents"]
    resources = ["arn:aws:logs:ca-central-1:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/paysafe-upf-dataops*:*"]
    effect = "Allow"
  }
  statement {
    actions   = ["logs:CreateLogGroup"]
    resources = ["arn:aws:logs:ca-central-1:${data.aws_caller_identity.current.account_id}:*"]
    effect = "Allow"
  }
  statement {
    actions   = ["ec2:CreateNetworkInterface","ec2:DescribeNetworkInterfaces","ec2:DeleteNetworkInterface",]
    resources = ["*"]
    effect = "Allow"
  }
}