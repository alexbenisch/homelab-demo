variable "hcloud_token" {
  description = "Hetzner Cloud API Token"
  type        = string
  sensitive   = true
}

variable "zone_name" {
  description = "DNS zone name"
  type        = string
  default     = "k8s-demo.de"
}

variable "default_ttl" {
  description = "Default TTL for DNS records"
  type        = number
  default     = 3600
}

variable "cluster_ip" {
  description = "IP address of the k3s cluster control plane"
  type        = string
  default     = ""
}

variable "subdomains" {
  description = "Map of subdomain names to their configurations"
  type = map(object({
    type    = string
    value   = string
    ttl     = optional(number)
    comment = optional(string)
  }))
  default = {}
}
