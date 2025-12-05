# DNS Module - Route 53 Records

# Create hosted zone if requested
resource "aws_route53_zone" "main" {
  count = var.create_zone ? 1 : 0
  name  = var.domain_name

  tags = {
    Name = var.domain_name
  }
}

# Use existing or created zone
locals {
  zone_id = var.create_zone ? aws_route53_zone.main[0].zone_id : var.zone_id
}

# A record pointing to ALB
resource "aws_route53_record" "main" {
  zone_id = local.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}
