variable "name" {
  type = string
}

variable "environment" {
  description = "staging or prod: the GHCR tag this VM follows."
  type        = string
}

variable "location" {
  type = string
}

variable "server_type" {
  type = string
}

variable "server_image" {
  type = string
}

variable "volume_name" {
  type = string
}

variable "volume_size_gb" {
  type = number
}

variable "ssh_key_ids" {
  type = list(string)
}

variable "image_repository" {
  type = string
}

variable "backup_bucket_name" {
  type = string
}

variable "object_storage_endpoint" {
  type = string
}

variable "labels" {
  type = map(string)
}
