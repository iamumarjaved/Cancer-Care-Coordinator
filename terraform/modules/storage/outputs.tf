output "efs_file_system_id" {
  value = aws_efs_file_system.main.id
}

output "efs_access_point_id" {
  value = aws_efs_access_point.chroma.id
}

output "efs_dns_name" {
  value = aws_efs_file_system.main.dns_name
}
