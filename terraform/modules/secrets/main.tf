# Secrets Module - AWS Secrets Manager

resource "aws_secretsmanager_secret" "app_secrets" {
  name = "${var.project_name}-${var.environment}-secrets"

  tags = {
    Name = "${var.project_name}-${var.environment}-secrets"
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    DATABASE_URL                       = var.database_url
    OPENAI_API_KEY                     = var.openai_api_key
    CLERK_SECRET_KEY                   = var.clerk_secret_key
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY  = var.clerk_publishable_key
    LANGSMITH_API_KEY                  = var.langsmith_api_key
    SENDGRID_API_KEY                   = var.sendgrid_api_key
  })
}
