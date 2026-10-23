variable "project_prefix" {
  description = "Prefix for every resource name (discovery report §3)."
  type        = string
  default     = "learnplat"
}

variable "location" {
  description = "Hetzner location; also the Object Storage region (discovery: fsn1)."
  type        = string
  default     = "fsn1"
}

variable "backup_daily_retention_days" {
  description = "Days the daily backup copies are kept (discovery: 30)."
  type        = number
  default     = 30
}

variable "backup_monthly_retention_days" {
  description = "Days the monthly backup copies are kept (discovery: 12 months)."
  type        = number
  default     = 366
}
