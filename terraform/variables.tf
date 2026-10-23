# Core parameters, defined once and passed to every module (rulebook T11). Values come from the
# approved discovery report (docs/deployment/discovery-report.md §2-3).

variable "project_prefix" {
  description = "Prefix for every resource name."
  type        = string
  default     = "learnplat"
}

variable "location" {
  description = "Hetzner location (Falkenstein, Germany)."
  type        = string
  default     = "fsn1"
}

variable "environments" {
  description = "One VM + data volume per environment."
  type = map(object({
    server_type    = string
    volume_size_gb = number
  }))
  default = {
    staging = { server_type = "cx22", volume_size_gb = 10 }
    prod    = { server_type = "cx22", volume_size_gb = 10 }
  }
}

variable "server_image" {
  description = "VM operating system image."
  type        = string
  default     = "ubuntu-24.04"
}

variable "image_repository" {
  description = "Container image the VMs follow (tags: staging, prod)."
  type        = string
  default     = "ghcr.io/flaviapop/learnplat"
}

# Required, no default: SSH is allowed ONLY from these addresses. An empty list would lock every
# operator out (rulebook ACL1), so plan/apply refuse to run until it is provided.
variable "operator_ip_addresses" {
  description = "Operator public IPs/CIDRs allowed to SSH (e.g. [\"203.0.113.7/32\"])."
  type        = list(string)
  validation {
    condition     = length(var.operator_ip_addresses) > 0 && alltrue([for cidr in var.operator_ip_addresses : can(cidrnetmask(cidr)) || can(cidrhost(cidr, 0))])
    error_message = "Provide at least one valid CIDR (e.g. 203.0.113.7/32)."
  }
}

variable "operator_ssh_public_keys" {
  description = "Map of key name => OpenSSH public key installed for root on every VM."
  type        = map(string)
  validation {
    condition     = length(var.operator_ssh_public_keys) > 0
    error_message = "Provide at least one operator SSH public key."
  }
}

# Written by terraform/bootstrap into bootstrap.auto.tfvars.
variable "backup_bucket_name" {
  description = "Object Storage bucket for the encrypted nightly backups."
  type        = string
}

variable "object_storage_endpoint" {
  description = "S3 endpoint of Hetzner Object Storage for the backups."
  type        = string
}
