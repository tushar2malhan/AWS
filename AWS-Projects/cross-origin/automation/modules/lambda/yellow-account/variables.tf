# declare variables

variable "region" {
  type        = string
  description = "region of test user id"
}

variable "handler" {
  type        = string
  description = "handler  with lambda function name"
  
}
variable "function_name" {
  type        = string
  description = " lambda function name "
}

variable "runtime" {
  type        = string
  description = " runtime of lambda function "
}

variable "lambda_timeout" {
  type        = string
  description = " timeout in seconds for lambda function "
}

variable "python_file" {
    type        = string
    description = "location of python file which needs to be zipped"
}

variable "output_path" {
    type        = string
    description = " python zipped file location "
}


variable "iam_policy_name_kinesis" {
    type        = string
    description = " name of iam policy for kinesis"
}

variable "iam_policy_name_asssume" {
    type        = string
    description = " name of iam policy for assume role "
}

variable "iam_role_name" {
    type        = string
    description = " name of iam role "
}

variable "event_rule_name" {
    type        = string
    description = " name of the event rule "
}

variable "account_id" {
  description = "Account in which the resource should be created"
  type        = string
}

variable "blue_account_id"{
    type        = string
    description = "It is id of account which is to be allowed access"
}


variable "grey_account_id"{
    type        = string
    description = "It is id of account which is to be allowed access"
}

variable "cross_account_id" {
  description = "Cross Account in which the resource is to be accessed"
  type        = string
}

variable "config_file_key" {
  description = " Flag json value from s3 bucket  Dataops properties "
  type        = string
}

