variable "hcloud_token" {
  description = "Hetzner Cloud API Token"
  type        = string
  sensitive   = true
}

variable "ssh_public_key" {
  description = "SSH public key for server access"
  type        = string
  default     = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAmm9jDoXxpMFSGUYFUCk56TaPPTxMRdgnTY9FCBwjF3 alex@tpad"
}

variable "location" {
  description = "Hetzner datacenter location"
  type        = string
  default     = "nbg1"
}

variable "server_type" {
  description = "Server type for all nodes"
  type        = string
  default     = "cpx11"
}

variable "control_plane_private_ip" {
  description = "Private IP for control plane node"
  type        = string
  default     = "10.0.1.10"
}

variable "worker1_private_ip" {
  description = "Private IP for worker 1 node"
  type        = string
  default     = "10.0.1.20"
}

variable "worker2_private_ip" {
  description = "Private IP for worker 2 node"
  type        = string
  default     = "10.0.1.21"
}

variable "network_ip_range" {
  description = "IP range for the private network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_ip_range" {
  description = "IP range for the subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "user_password" {
  description = "Password for alex user (will be hashed)"
  type        = string
  sensitive   = true
  default     = "123password"
}
