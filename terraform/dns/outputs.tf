output "zone_id" {
  description = "ID of the DNS zone"
  value       = hcloud_zone.k8s_demo.id
}

output "zone_name" {
  description = "Name of the DNS zone"
  value       = hcloud_zone.k8s_demo.name
}

output "nameservers" {
  description = "Nameservers for the zone"
  value       = hcloud_zone.k8s_demo.nameservers
}

output "dns_records" {
  description = "List of configured DNS records"
  value = {
    for name, config in var.subdomains :
    "${name}.${var.zone_name}" => {
      type  = config.type
      value = config.value
      ttl   = config.ttl != null ? config.ttl : var.default_ttl
    }
  }
}

output "dns_summary" {
  description = "Summary of DNS configuration"
  value = <<-EOT
    DNS Zone: ${hcloud_zone.k8s_demo.name}
    Zone ID: ${hcloud_zone.k8s_demo.id}
    TTL: ${hcloud_zone.k8s_demo.ttl}

    Nameservers:
    ${join("\n    ", hcloud_zone.k8s_demo.nameservers)}

    Configured Records:
    ${join("\n    ", [for name, config in var.subdomains : "${name}.${var.zone_name} -> ${config.type} ${config.value}"])}
  EOT
}
