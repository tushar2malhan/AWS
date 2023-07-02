module "lambda_builder" {
  source                    = "../../../modules/lambda/yellow-account"
  function_name             = "Paysafe-upf-dataops-emrEventsDetails-yellow"
  region                    = "ca-central-1"
  python_file               = "../../../modules/lambda/yellow-account/lambda_function_yellow.py"
  handler                   = "lambda_function_yellow.lambda_handler"
  runtime                   = "python3.8"
  output_path               = "../../../modules/lambda/yellow-account/lambda_function_yellow.zip"
  iam_policy_name_kinesis   = "Paysafe-upf-dataops-aws-kinesis-put-policy-yellow"    
  iam_policy_name_asssume   = "Paysafe-upf-dataops-aws-assume-role-policy-yellow"
  iam_role_name             = "Paysafe-upf-dataops-iam-role-yellow-acc"
  event_rule_name           = "Paysafe-upf-dataops-emr-detail-rule-yellow"
  lambda_timeout            = "300"
  account_id                = "195255969266"
  grey_account_id           = "245535966659"
  blue_account_id           = "452253236614"
  cross_account_id          = "452253236614"
   config_file_key           = "paysafe-upf-dataops-lambda-emr-details-audit-trail/prod/yellow/flag-execute-lambda.json"  
}
