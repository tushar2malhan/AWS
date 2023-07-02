provider "aws" {
  region  = "ca-central-1"
  assume_role {
    role_arn     = "arn:aws:iam::541292993345:role/paysafe-aws-unity-dataops-tf-deployer-role"
    session_name = "bamboo-deployer"
  }
}

terraform {
  backend "s3" {
    bucket         = "paysafe-unity-dataops-765683906439-ca-central-1-tf-states"
    key            = "mon-dev/paysafe-upf-dataops-alert_dashboard_/terraform.tfstate"
    region         = "ca-central-1"
    encrypt        = true
    dynamodb_table = "unity-dataops-terraform-locks"
  }
}