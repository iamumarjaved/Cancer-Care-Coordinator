variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "enable_https" {
  type    = bool
  default = false
}

variable "certificate_arn" {
  type    = string
  default = ""
}
