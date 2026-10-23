terraform {
  required_providers {
    hcloud = {
      source = "hetznercloud/hcloud"
    }
  }
}

# The data volume is created first, so its id (stable device path) can go into cloud-init;
# it is attached afterwards. Left unformatted: cloud-init encrypts it with LUKS2 and creates the
# ext4 filesystem inside (deploy plan, encryption at rest). SQLite lives on it at /data.
resource "hcloud_volume" "data" {
  name      = var.volume_name
  location  = var.location
  size      = var.volume_size_gb
  automount = false
  labels    = var.labels
}

resource "hcloud_server" "this" {
  name        = var.name
  server_type = var.server_type
  image       = var.server_image
  location    = var.location
  ssh_keys    = var.ssh_key_ids
  labels      = var.labels

  user_data = templatefile("${path.module}/cloud-init.yaml.tftpl", {
    environment             = var.environment
    image_repository        = var.image_repository
    backup_bucket_name      = var.backup_bucket_name
    object_storage_endpoint = var.object_storage_endpoint
    volume_device           = "/dev/disk/by-id/scsi-0HC_Volume_${hcloud_volume.data.id}"
    watch_script            = file("${path.module}/../../../deploy/watch.sh")
    data_volume_script      = file("${path.module}/../../../deploy/data-volume.sh")
    logrotate_conf          = file("${path.module}/../../../deploy/logrotate.conf")
    watch_service           = file("${path.module}/../../../deploy/systemd/learnplat-watch.service")
    watch_timer             = file("${path.module}/../../../deploy/systemd/learnplat-watch.timer")
    backup_service          = file("${path.module}/../../../deploy/systemd/learnplat-backup.service")
    backup_timer            = file("${path.module}/../../../deploy/systemd/learnplat-backup.timer")
  })

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  lifecycle {
    # cloud-init only runs at first boot; later script changes ship inside the image bundle.
    ignore_changes = [user_data, ssh_keys]
  }
}

resource "hcloud_volume_attachment" "data" {
  volume_id = hcloud_volume.data.id
  server_id = hcloud_server.this.id
  automount = false
}
