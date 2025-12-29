# SSH Key
resource "hcloud_ssh_key" "default" {
  name       = "alex-tpad"
  public_key = var.ssh_public_key
}

# Network
resource "hcloud_network" "homelab" {
  name     = "homelab-demo-network"
  ip_range = var.network_ip_range
}

resource "hcloud_network_subnet" "homelab" {
  network_id   = hcloud_network.homelab.id
  type         = "cloud"
  network_zone = "eu-central"
  ip_range     = var.subnet_ip_range
}

# Firewall
resource "hcloud_firewall" "homelab" {
  name = "homelab-demo-firewall"

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = [
      "0.0.0.0/0",
      "::/0"
    ]
  }

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "80"
    source_ips = [
      "0.0.0.0/0",
      "::/0"
    ]
  }

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "443"
    source_ips = [
      "0.0.0.0/0",
      "::/0"
    ]
  }

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "6443"
    source_ips = [
      "0.0.0.0/0",
      "::/0"
    ]
  }
}

# Control Plane Server
resource "hcloud_server" "control_plane" {
  name        = "ctrl"
  image       = "ubuntu-22.04"
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.default.id]
  firewall_ids = [hcloud_firewall.homelab.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  user_data = templatefile("${path.module}/cloud-init/control-plane.tftpl", {
    ssh_public_key = var.ssh_public_key
    user_password  = var.user_password
  })

  labels = {
    role = "control-plane"
  }
}

resource "hcloud_server_network" "control_plane" {
  server_id  = hcloud_server.control_plane.id
  network_id = hcloud_network.homelab.id
  ip         = var.control_plane_private_ip
}

# Wait for control plane to be ready and get k3s token
resource "null_resource" "get_k3s_token" {
  depends_on = [hcloud_server.control_plane]

  provisioner "local-exec" {
    command = <<-EOT
      echo "Waiting for k3s to initialize on control plane..."
      sleep 120
      echo "K3S_TOKEN will be available at /var/lib/rancher/k3s/server/node-token on control plane"
    EOT
  }
}

# Worker 1 Server
resource "hcloud_server" "worker1" {
  name        = "wrkr1"
  image       = "ubuntu-22.04"
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.default.id]
  firewall_ids = [hcloud_firewall.homelab.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  user_data = templatefile("${path.module}/cloud-init/worker.tftpl", {
    hostname              = "wrkr1"
    node_name             = "wrkr1"
    ssh_public_key        = var.ssh_public_key
    user_password         = var.user_password
    control_plane_ip      = var.control_plane_private_ip
  })

  labels = {
    role = "worker"
  }

  depends_on = [null_resource.get_k3s_token]
}

resource "hcloud_server_network" "worker1" {
  server_id  = hcloud_server.worker1.id
  network_id = hcloud_network.homelab.id
  ip         = var.worker1_private_ip
}

# Worker 2 Server
resource "hcloud_server" "worker2" {
  name        = "wrkr2"
  image       = "ubuntu-22.04"
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.default.id]
  firewall_ids = [hcloud_firewall.homelab.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  user_data = templatefile("${path.module}/cloud-init/worker.tftpl", {
    hostname              = "wrkr2"
    node_name             = "wrkr2"
    ssh_public_key        = var.ssh_public_key
    user_password         = var.user_password
    control_plane_ip      = var.control_plane_private_ip
  })

  labels = {
    role = "worker"
  }

  depends_on = [null_resource.get_k3s_token]
}

resource "hcloud_server_network" "worker2" {
  server_id  = hcloud_server.worker2.id
  network_id = hcloud_network.homelab.id
  ip         = var.worker2_private_ip
}
