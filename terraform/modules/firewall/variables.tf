variable "name" {
  type = string
}

variable "operator_ip_addresses" {
  type = list(string)
}

variable "labels" {
  type = map(string)
}

variable "apply_to_label" {
  description = "Label selector of the servers this firewall protects."
  type        = string
}
