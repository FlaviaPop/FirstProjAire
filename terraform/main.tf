locals {
  # Default labels on every resource (rulebook TAG4; Hetzner calls tags "labels").
  default_labels = {
    project    = var.project_prefix
    managed_by = "terraform"
  }
}

resource "hcloud_ssh_key" "operator" {
  for_each   = var.operator_ssh_public_keys
  name       = "${var.project_prefix}-${each.key}"
  public_key = each.value
  labels     = local.default_labels
}

module "firewall" {
  source                = "./modules/firewall"
  name                  = "${var.project_prefix}-fw"
  operator_ip_addresses = var.operator_ip_addresses
  labels                = local.default_labels
  apply_to_label        = "project=${var.project_prefix}"
}

module "server" {
  source   = "./modules/server"
  for_each = var.environments

  name                    = "${var.project_prefix}-${each.key}"
  environment             = each.key
  location                = var.location
  server_type             = each.value.server_type
  server_image            = var.server_image
  volume_name             = "${var.project_prefix}-${each.key}-data"
  volume_size_gb          = each.value.volume_size_gb
  ssh_key_ids             = [for key in hcloud_ssh_key.operator : key.id]
  image_repository        = var.image_repository
  backup_bucket_name      = var.backup_bucket_name
  object_storage_endpoint = var.object_storage_endpoint
  labels                  = merge(local.default_labels, { environment = each.key })

  # The firewall (label selector) exists before any server boots.
  depends_on = [module.firewall]
}
