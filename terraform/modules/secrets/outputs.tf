output "secrets_arn" {
  value = aws_secretsmanager_secret.app_secrets.arn
}

output "secrets_name" {
  value = aws_secretsmanager_secret.app_secrets.name
}
