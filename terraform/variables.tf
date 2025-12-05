# Cancer Care Coordinator - Terraform Variables

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cancer-care"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "healthcare.umarjaved.me"
}

variable "enable_https" {
  description = "Enable HTTPS with custom domain (requires Route 53)"
  type        = bool
  default     = false
}

variable "create_route53_zone" {
  description = "Create a new Route 53 hosted zone"
  type        = bool
  default     = false
}

variable "route53_zone_id" {
  description = "Existing Route 53 hosted zone ID (if not creating new)"
  type        = string
  default     = ""
}

# Database credentials
variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "cancercare_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

# Application secrets
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "clerk_secret_key" {
  description = "Clerk secret key"
  type        = string
  sensitive   = true
}

variable "clerk_publishable_key" {
  description = "Clerk publishable key"
  type        = string
  sensitive   = true
}

variable "langsmith_api_key" {
  description = "LangSmith API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "sendgrid_api_key" {
  description = "SendGrid API key"
  type        = string
  sensitive   = true
  default     = ""
}
