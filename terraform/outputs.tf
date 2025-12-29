output "control_plane_ipv4" {
  description = "Public IPv4 address of control plane"
  value       = hcloud_server.control_plane.ipv4_address
}

output "control_plane_private_ip" {
  description = "Private IP address of control plane"
  value       = hcloud_server_network.control_plane.ip
}

output "worker1_ipv4" {
  description = "Public IPv4 address of worker 1"
  value       = hcloud_server.worker1.ipv4_address
}

output "worker1_private_ip" {
  description = "Private IP address of worker 1"
  value       = hcloud_server_network.worker1.ip
}

output "worker2_ipv4" {
  description = "Public IPv4 address of worker 2"
  value       = hcloud_server.worker2.ipv4_address
}

output "worker2_private_ip" {
  description = "Private IP address of worker 2"
  value       = hcloud_server_network.worker2.ip
}

output "ssh_connection_control_plane" {
  description = "SSH command to connect to control plane"
  value       = "ssh alex@${hcloud_server.control_plane.ipv4_address}"
}

output "ssh_connection_worker1" {
  description = "SSH command to connect to worker 1"
  value       = "ssh alex@${hcloud_server.worker1.ipv4_address}"
}

output "ssh_connection_worker2" {
  description = "SSH command to connect to worker 2"
  value       = "ssh alex@${hcloud_server.worker2.ipv4_address}"
}

output "next_steps" {
  description = "Next steps after deployment"
  value       = <<-EOT
    Deployment complete!

    1. Wait 2-3 minutes for cloud-init to complete on all servers

    2. Connect to control plane:
       ssh alex@${hcloud_server.control_plane.ipv4_address}

    3. Get k3s token (needed for workers):
       sudo cat /var/lib/rancher/k3s/server/node-token

    4. Configure workers with the k3s token:
       # On each worker, edit and run:
       ssh alex@${hcloud_server.worker1.ipv4_address}
       sudo nano /root/install-k3s-agent.sh
       # Add the token, then run:
       sudo /root/install-k3s-agent.sh

    5. Verify cluster:
       kubectl get nodes

    6. Get kubeconfig:
       scp alex@${hcloud_server.control_plane.ipv4_address}:/home/alex/.kube/config ~/.kube/config
       sed -i 's/127.0.0.1/${hcloud_server.control_plane.ipv4_address}/g' ~/.kube/config

    Default password: 123password (change immediately!)
  EOT
}
