terraform {
  required_version = ">= 1.6.0"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.49"
    }
  }
  # Remote state in Hetzner Object Storage (rulebook T1). Values come from backend.hcl, which
  # terraform/bootstrap writes:  terraform init -backend-config=backend.hcl
  # Credentials: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY = Object Storage keys.
  backend "s3" {}
}

# Token: HCLOUD_TOKEN environment variable (never in code or tfvars).
provider "hcloud" {}
