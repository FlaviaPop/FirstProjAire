terraform {
  required_providers {
    hcloud = {
      source = "hetznercloud/hcloud"
    }
  }
}

# Inbound: HTTP/HTTPS from anywhere (Let's Encrypt + users), SSH only from operators, ICMP.
# Applied to every server carrying the project label, so new servers are covered automatically.
resource "hcloud_firewall" "this" {
  name   = var.name
  labels = var.labels

  rule {
    description = "HTTP (ACME challenge + redirect to HTTPS)"
    direction   = "in"
    protocol    = "tcp"
    port        = "80"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    description = "HTTPS"
    direction   = "in"
    protocol    = "tcp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    description = "SSH from operators only"
    direction   = "in"
    protocol    = "tcp"
    port        = "22"
    source_ips  = var.operator_ip_addresses
  }

  rule {
    description = "ICMP (ping, path MTU)"
    direction   = "in"
    protocol    = "icmp"
    source_ips  = ["0.0.0.0/0", "::/0"]
  }

  apply_to {
    label_selector = var.apply_to_label
  }
}
