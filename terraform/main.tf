# Cancer Care Coordinator - Main Terraform Configuration

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Networking Module
module "networking" {
  source = "./modules/networking"

  project_name        = var.project_name
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = slice(data.aws_availability_zones.available.names, 0, 2)
}

# Security Module
module "security" {
  source = "./modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.networking.vpc_id
}

# ECR Module
module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

# SSL Certificate Module
module "ssl" {
  source = "./modules/ssl"

  domain_name = var.domain_name
  zone_id     = var.route53_zone_id
}

# Database Module
module "database" {
  source = "./modules/database"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id  = module.security.rds_security_group_id
  db_username        = var.db_username
  db_password        = var.db_password
}

# Storage Module (EFS for ChromaDB)
module "storage" {
  source = "./modules/storage"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id  = module.security.efs_security_group_id
}

# Secrets Manager Module
module "secrets" {
  source = "./modules/secrets"

  project_name                       = var.project_name
  environment                        = var.environment
  database_url                       = module.database.connection_string
  openai_api_key                     = var.openai_api_key
  clerk_secret_key                   = var.clerk_secret_key
  clerk_publishable_key              = var.clerk_publishable_key
  langsmith_api_key                  = var.langsmith_api_key
  sendgrid_api_key                   = var.sendgrid_api_key
}

# Load Balancer Module
module "loadbalancer" {
  source = "./modules/loadbalancer"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.networking.vpc_id
  public_subnet_ids   = module.networking.public_subnet_ids
  security_group_id   = module.security.alb_security_group_id
  certificate_arn     = module.ssl.certificate_arn
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"

  project_name         = var.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  vpc_id               = module.networking.vpc_id
  private_subnet_ids   = module.networking.private_subnet_ids
  backend_sg_id        = module.security.backend_security_group_id
  frontend_sg_id       = module.security.frontend_security_group_id
  backend_ecr_url      = module.ecr.backend_repository_url
  frontend_ecr_url     = module.ecr.frontend_repository_url
  alb_target_group_backend_arn  = module.loadbalancer.backend_target_group_arn
  alb_target_group_frontend_arn = module.loadbalancer.frontend_target_group_arn
  efs_file_system_id   = module.storage.efs_file_system_id
  efs_access_point_id  = module.storage.efs_access_point_id
  secrets_arn          = module.secrets.secrets_arn
  domain_name          = var.domain_name
}

# DNS Module
module "dns" {
  source = "./modules/dns"

  domain_name = var.domain_name
  zone_id     = var.route53_zone_id
  alb_dns_name = module.loadbalancer.alb_dns_name
  alb_zone_id  = module.loadbalancer.alb_zone_id
}
