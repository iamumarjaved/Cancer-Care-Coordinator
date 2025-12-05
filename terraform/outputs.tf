# Cancer Care Coordinator - Terraform Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.loadbalancer.alb_dns_name
}

output "application_url" {
  description = "Application URL"
  value       = var.enable_https ? "https://${var.domain_name}" : "http://${module.loadbalancer.alb_dns_name}"
}

output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL"
  value       = module.ecr.backend_repository_url
}

output "frontend_ecr_repository_url" {
  description = "Frontend ECR repository URL"
  value       = module.ecr.frontend_repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.database.endpoint
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "backend_service_name" {
  description = "Backend ECS service name"
  value       = module.ecs.backend_service_name
}

output "frontend_service_name" {
  description = "Frontend ECS service name"
  value       = module.ecs.frontend_service_name
}

output "route53_nameservers" {
  description = "Route 53 nameservers (if zone was created)"
  value       = var.enable_https && var.create_route53_zone ? module.dns[0].nameservers : []
}
