variable "domain_name" {
  type = string
}

variable "create_zone" {
  type    = bool
  default = false
}

variable "zone_id" {
  type    = string
  default = ""
}

variable "alb_dns_name" {
  type = string
}

variable "alb_zone_id" {
  type = string
}
