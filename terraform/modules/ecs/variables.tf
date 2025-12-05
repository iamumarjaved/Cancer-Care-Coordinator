variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "backend_sg_id" {
  type = string
}

variable "frontend_sg_id" {
  type = string
}

variable "backend_ecr_url" {
  type = string
}

variable "frontend_ecr_url" {
  type = string
}

variable "alb_target_group_backend_arn" {
  type = string
}

variable "alb_target_group_frontend_arn" {
  type = string
}

variable "efs_file_system_id" {
  type = string
}

variable "efs_access_point_id" {
  type = string
}

variable "secrets_arn" {
  type = string
}

variable "domain_name" {
  type = string
}
