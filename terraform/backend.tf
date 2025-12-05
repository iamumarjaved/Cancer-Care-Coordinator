# Terraform State Backend Configuration
# Run 'terraform init' after creating the S3 bucket and DynamoDB table

terraform {
  backend "s3" {
    bucket         = "cancer-care-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "cancer-care-terraform-locks"
  }
}
