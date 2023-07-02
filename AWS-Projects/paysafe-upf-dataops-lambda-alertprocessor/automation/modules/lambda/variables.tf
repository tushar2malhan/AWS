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

variable "dynamodb_name" {
    type        = string
    description = " name of dynamodb table "
}

variable "iam_policy_name" {
    type        = string
    description = " name of iam policy "
}

variable "iam_role_name" {
    type        = string
    description = " name of iam role "
}

variable "event_rule_name" {
    type        = string
    description = " name of the event rule "
}

variable "blue_account_id"{
    type        = string
    description = "It is id of account which is to be allowed acces"
    default     = "195255969266"
}

variable "yellow_account_id"{
    type        = string
    description = "It is id of account which is to be allowed acces"
    default     = "195255969266"
}

variable "grey_account_id"{
    type        = string
    description = "It is id of account which is to be allowed acces"
    default     = "195255969266"
}