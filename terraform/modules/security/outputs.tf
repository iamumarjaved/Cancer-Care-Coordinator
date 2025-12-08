output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

output "backend_security_group_id" {
  value = aws_security_group.backend.id
}

output "frontend_security_group_id" {
  value = aws_security_group.frontend.id
}

output "efs_security_group_id" {
  value = aws_security_group.efs.id
}
