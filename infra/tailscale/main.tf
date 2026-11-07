terraform {
  required_providers {
    tailscale = {
      source  = "tailscale/tailscale"
      version = "0.29.2"
    }
  }
}

provider "tailscale" {}

resource "tailscale_acl" "hermes" {
  acl = file("${path.module}/policy.hujson")
}
