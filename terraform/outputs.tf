output "servers" {
  description = "Per environment: server name and public IPs (for the manual DNS A/AAAA records)."
  value = {
    for env, server in module.server : env => {
      name = server.name
      ipv4 = server.ipv4_address
      ipv6 = server.ipv6_address
    }
  }
}

output "firewall" {
  value = module.firewall.name
}
