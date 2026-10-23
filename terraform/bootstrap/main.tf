# Bootstrap (run once, LOCAL state - rulebook B1): the Object Storage buckets the main Terraform
# needs before `terraform init` (state) and the nightly backups write to. Idempotent (B3).
# Hetzner Object Storage is S3-compatible; the AWS provider talks to it through a custom endpoint.

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

# Credentials: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY = Hetzner Object Storage keys.
provider "aws" {
  region                      = var.location
  skip_region_validation      = true
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  s3_use_path_style           = true
  endpoints {
    s3 = local.endpoint
  }
}

locals {
  endpoint = "https://${var.location}.your-objectstorage.com"
}

# Bucket names are unique across all Hetzner customers in a location (rulebook NC1/NC2): the
# names from discovery get a stable random suffix, output for the main config (NC5).
resource "random_string" "suffix" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_s3_bucket" "tfstate" {
  bucket = "${var.project_prefix}-tfstate-${random_string.suffix.result}"
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "backups" {
  bucket = "${var.project_prefix}-backups-${random_string.suffix.result}"
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Retention (discovery): daily copies 30 days, monthly copies 12 months, old versions 7 days.
# Keys start with the kind (daily/<env>/..., monthly/<env>/...): lifecycle prefixes have no
# wildcards, so the kind must come first for one rule per kind.
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket     = aws_s3_bucket.backups.id
  depends_on = [aws_s3_bucket_versioning.backups]

  rule {
    id     = "daily"
    status = "Enabled"
    filter {
      prefix = "daily/"
    }
    expiration {
      days = var.backup_daily_retention_days
    }
    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }

  rule {
    id     = "monthly"
    status = "Enabled"
    filter {
      prefix = "monthly/"
    }
    expiration {
      days = var.backup_monthly_retention_days
    }
    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

# Hand-over to the main configuration: partial backend config + the backup bucket name.
resource "local_file" "backend_hcl" {
  filename        = "${path.module}/../backend.hcl"
  file_permission = "0644"
  content         = <<-HCL
    bucket                      = "${aws_s3_bucket.tfstate.bucket}"
    key                         = "${var.project_prefix}/terraform.tfstate"
    region                      = "${var.location}"
    endpoints                   = { s3 = "${local.endpoint}" }
    use_path_style              = true
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
  HCL
}

resource "local_file" "bootstrap_tfvars" {
  filename        = "${path.module}/../bootstrap.auto.tfvars"
  file_permission = "0644"
  content         = <<-HCL
    backup_bucket_name = "${aws_s3_bucket.backups.bucket}"
    object_storage_endpoint = "${local.endpoint}"
  HCL
}
