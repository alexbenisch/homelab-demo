# Import existing DNS zone or create new one
# Note: If zone already exists, import it with:
# terraform import hcloud_zone.k8s_demo <zone-id>

resource "hcloud_zone" "k8s_demo" {
  name = var.zone_name
  mode = "primary"
  ttl  = var.default_ttl

  labels = {
    managed-by = "terraform"
    environment = "homelab"
  }

  # Dynamic rrsets for A records (subdomains)
  dynamic "rrsets" {
    for_each = {
      for name, config in var.subdomains : name => config
      if config.type == "A"
    }

    content {
      name = rrsets.key
      type = "A"
      ttl  = rrsets.value.ttl != null ? rrsets.value.ttl : var.default_ttl

      records {
        value   = rrsets.value.value
        comment = rrsets.value.comment
      }
    }
  }

  # Dynamic rrsets for AAAA records
  dynamic "rrsets" {
    for_each = {
      for name, config in var.subdomains : name => config
      if config.type == "AAAA"
    }

    content {
      name = rrsets.key
      type = "AAAA"
      ttl  = rrsets.value.ttl != null ? rrsets.value.ttl : var.default_ttl

      records {
        value   = rrsets.value.value
        comment = rrsets.value.comment
      }
    }
  }

  # Dynamic rrsets for CNAME records
  dynamic "rrsets" {
    for_each = {
      for name, config in var.subdomains : name => config
      if config.type == "CNAME"
    }

    content {
      name = rrsets.key
      type = "CNAME"
      ttl  = rrsets.value.ttl != null ? rrsets.value.ttl : var.default_ttl

      records {
        value   = rrsets.value.value
        comment = rrsets.value.comment
      }
    }
  }

  # Dynamic rrsets for TXT records
  dynamic "rrsets" {
    for_each = {
      for name, config in var.subdomains : name => config
      if config.type == "TXT"
    }

    content {
      name = rrsets.key
      type = "TXT"
      ttl  = rrsets.value.ttl != null ? rrsets.value.ttl : var.default_ttl

      records {
        value   = rrsets.value.value
        comment = rrsets.value.comment
      }
    }
  }

  # Dynamic rrsets for MX records
  dynamic "rrsets" {
    for_each = {
      for name, config in var.subdomains : name => config
      if config.type == "MX"
    }

    content {
      name = rrsets.key
      type = "MX"
      ttl  = rrsets.value.ttl != null ? rrsets.value.ttl : var.default_ttl

      records {
        value   = rrsets.value.value
        comment = rrsets.value.comment
      }
    }
  }

  delete_protection = false
}
