terraform {
  required_version = ">= 1.8.2"

  backend "s3" {
    bucket = "sterliakov"
    key    = "tg-forwarder/terraform/terraform.tfstate"
    region = "us-east-2"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.60.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
