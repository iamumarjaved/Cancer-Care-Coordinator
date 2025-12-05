output "fqdn" {
  value = aws_route53_record.main.fqdn
}

output "zone_id" {
  value = var.create_zone ? aws_route53_zone.main[0].zone_id : var.zone_id
}

output "nameservers" {
  value = var.create_zone ? aws_route53_zone.main[0].name_servers : []
}
