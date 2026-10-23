output "name" {
  value = hcloud_server.this.name
}

output "ipv4_address" {
  value = hcloud_server.this.ipv4_address
}

output "ipv6_address" {
  value = hcloud_server.this.ipv6_address
}

output "volume_id" {
  value = hcloud_volume.data.id
}
