module "lambda_builder" {
  source                    = "../../../modules/lambda"
  function_name             = "Paysafe-upf-dataops-alertDashboardEvents"
  region                    = "ca-central-1"
  python_file               = "../../../modules/lambda/lambda_function.py"
  handler                   = "lambda_function.lambda_handler"
  runtime                   = "python3.8"
  output_path               = "../../../modules/lambda/lambda_function.zip"
  dynamodb_name             = "alertDashboard_logs"
  iam_policy_name           = "Paysafe-upf-dataops-aws_cloudwatch_dynamic_policy"
  iam_role_name             = "Paysafe-upf-dataops-alert-dashboard-iam-role"
  event_rule_name           = "Paysafe-upf-dataops-alertDashboard"
  lambda_timeout            = "300"
}