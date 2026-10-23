output "tfstate_bucket" {
  description = "State bucket (written to ../backend.hcl)."
  value       = aws_s3_bucket.tfstate.bucket
}

output "backup_bucket" {
  description = "Backup bucket (written to ../bootstrap.auto.tfvars)."
  value       = aws_s3_bucket.backups.bucket
}

output "object_storage_endpoint" {
  value = local.endpoint
}
