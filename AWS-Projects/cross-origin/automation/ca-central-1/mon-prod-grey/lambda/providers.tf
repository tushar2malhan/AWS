provider "aws" {
  region  = "ca-central-1"
  alias = "grey_account"
  assume_role {
    role_arn     = "arn:aws:iam::245535966659:role/paysafe-aws-unity-dataops-tf-deployer-role"
    session_name = "bamboo-deployer"
  }
}

terraform {
  backend "s3" {
    bucket         = "paysafe-unity-dataops-765683906439-ca-central-1-tf-states"
    key            = "mon-prod-grey/paysafe-upf-dataops-emr-details/terraform.tfstate"
    region         = "ca-central-1"
    encrypt        = true
    dynamodb_table = "unity-dataops-terraform-locks"
  }
}