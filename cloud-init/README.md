# Manual Server Setup with Cloud-Init

> **⚠️ LEGACY APPROACH**: This manual setup is now deprecated in favor of automated Terraform deployment via GitHub Actions.
>
> **For automated deployment, see:** [`terraform/README.md`](../terraform/README.md)
>
> This directory is kept for reference and manual testing purposes.

This directory contains cloud-init configuration files for manually creating k3s cluster servers on Hetzner Cloud.

## Prerequisites

- Hetzner Cloud account
- DNS zone configured (k8s-demo.de)
- SSH key: `alex@tpad` (already uploaded to Hetzner)

## Network Setup

### 1. Create Private Network

In Hetzner Cloud Console:
1. Go to **Networks** → **Create Network**
2. Configure:
   - **Name**: `homelab-demo-network`
   - **IP Range**: `10.0.0.0/16`
   - **Network Zone**: `eu-central`
3. Add subnet:
   - **IP Range**: `10.0.1.0/24`
   - **Type**: `Cloud`
4. Click **Create & Buy Now**

## Server Creation

### 2. Create Control Plane Node

1. Go to **Servers** → **Add Server**
2. Configure:
   - **Location**: Nuremberg (nbg1)
   - **Image**: Ubuntu 22.04
   - **Type**: CPX11 (2 vCPU, 2 GB RAM)
   - **Networking**:
     - ✅ Enable IPv4
     - ✅ Enable IPv6
     - ✅ Attach to network: `homelab-demo-network`
     - Private IP: `10.0.1.10` (assign manually)
   - **SSH Keys**: Select `alex@tpad`
   - **Cloud-init**: Copy content from `cloud-init/control-plane.yaml`
   - **Name**: `ctrl`
3. Click **Create & Buy Now**

**Wait for the server to finish cloud-init** (about 2-3 minutes):
```bash
# SSH into control plane
ssh alex@<CONTROL_PLANE_PUBLIC_IP>
# Password: 123password

# Check cloud-init status
sudo cloud-init status

# Check k3s status
sudo systemctl status k3s
kubectl get nodes

# Get the node token for workers
sudo cat /root/k3s-token
```

**Save the K3S token** - you'll need it for worker nodes!

### 3. Create Worker Node 1

1. Go to **Servers** → **Add Server**
2. Configure:
   - **Location**: Nuremberg (nbg1)
   - **Image**: Ubuntu 22.04
   - **Type**: CPX11 (2 vCPU, 2 GB RAM)
   - **Networking**:
     - ✅ Enable IPv4
     - ✅ Enable IPv6
     - ✅ Attach to network: `homelab-demo-network`
     - Private IP: `10.0.1.20` (assign manually)
   - **SSH Keys**: Select `alex@tpad`
   - **Cloud-init**: Copy content from `cloud-init/worker-1.yaml`
   - **Name**: `wrkr1`
3. Click **Create & Buy Now**

**After server is created:**
```bash
# SSH into worker-1
ssh alex@<WORKER1_PUBLIC_IP>
# Password: 123password

# Edit the k3s agent installation script
sudo nano /root/install-k3s-agent.sh

# Replace these values:
#   <CONTROL_PLANE_PRIVATE_IP> → 10.0.1.10
#   <K3S_TOKEN_FROM_CONTROL_PLANE> → (paste token from control plane)

# Run the installation
sudo /root/install-k3s-agent.sh

# Verify on control plane
# ssh alex@<CONTROL_PLANE_PUBLIC_IP>
# kubectl get nodes
```

### 4. Create Worker Node 2

1. Go to **Servers** → **Add Server**
2. Configure:
   - **Location**: Nuremberg (nbg1)
   - **Image**: Ubuntu 22.04
   - **Type**: CPX11 (2 vCPU, 2 GB RAM)
   - **Networking**:
     - ✅ Enable IPv4
     - ✅ Enable IPv6
     - ✅ Attach to network: `homelab-demo-network`
     - Private IP: `10.0.1.21` (assign manually)
   - **SSH Keys**: Select `alex@tpad`
   - **Cloud-init**: Copy content from `cloud-init/worker-2.yaml`
   - **Name**: `wrkr2`
3. Click **Create & Buy Now**

**After server is created:**
```bash
# SSH into worker-2
ssh alex@<WORKER2_PUBLIC_IP>
# Password: 123password

# Edit the k3s agent installation script
sudo nano /root/install-k3s-agent.sh

# Replace these values:
#   <CONTROL_PLANE_PRIVATE_IP> → 10.0.1.10
#   <K3S_TOKEN_FROM_CONTROL_PLANE> → (paste token from control plane)

# Run the installation
sudo /root/install-k3s-agent.sh
```

## Verification

On the control plane, verify all nodes are ready:

```bash
ssh alex@<CONTROL_PLANE_PUBLIC_IP>
kubectl get nodes

# Expected output:
# NAME     STATUS   ROLES                  AGE   VERSION
# ctrl     Ready    control-plane,master   10m   v1.28.5+k3s1
# wrkr1    Ready    <none>                 5m    v1.28.5+k3s1
# wrkr2    Ready    <none>                 5m    v1.28.5+k3s1
```

## Get Kubeconfig

Copy the kubeconfig from the control plane to your local machine:

```bash
# On control plane
cat /home/alex/.kube/config

# On your local machine
mkdir -p ~/.kube
scp alex@<CONTROL_PLANE_PUBLIC_IP>:/home/alex/.kube/config ~/.kube/config

# Edit the kubeconfig to use the public IP
sed -i 's/127.0.0.1/<CONTROL_PLANE_PUBLIC_IP>/g' ~/.kube/config

# Test
kubectl get nodes
```

## Next Steps

1. **Change passwords** on first login
2. **Setup DNS records** (use terraform/dns.tf or manual setup)
3. **Deploy nginx-ingress**: `kubectl apply -f kubernetes/infrastructure/ingress-nginx/`
4. **Deploy cert-manager**: Follow `kubernetes/infrastructure/cert-manager/README.md`
5. **Deploy applications**: `kubectl apply -f kubernetes/apps/homer/`

## Firewall Rules (Optional)

Create a firewall in Hetzner Cloud Console:

**Name**: `homelab-demo-firewall`

**Inbound Rules**:
- SSH: Port 22, Source: 0.0.0.0/0, ::/0
- HTTP: Port 80, Source: 0.0.0.0/0, ::/0
- HTTPS: Port 443, Source: 0.0.0.0/0, ::/0
- Kubernetes API: Port 6443, Source: 0.0.0.0/0, ::/0

**Outbound Rules**:
- Allow all

**Apply to**:
- ctrl
- wrkr1
- wrkr2

## Troubleshooting

### Cloud-init not completing

```bash
# Check cloud-init logs
sudo tail -f /var/log/cloud-init-output.log

# Check cloud-init status
sudo cloud-init status --long
```

### Worker node not joining

```bash
# On worker: Check k3s-agent logs
sudo journalctl -u k3s-agent -f

# Verify network connectivity to control plane
ping 10.0.1.10
curl -k https://10.0.1.10:6443
```

### k3s not starting

```bash
# Check k3s logs
sudo journalctl -u k3s -f          # On control plane
sudo journalctl -u k3s-agent -f    # On workers

# Restart k3s
sudo systemctl restart k3s         # On control plane
sudo systemctl restart k3s-agent   # On workers
```

## Cost Estimate

- 3x CPX11 servers: ~€13.50/month
- Network: Free
- Traffic: 20 TB included per server
- **Total**: ~€13.50/month

## Security Notes

- ⚠️ Default password is `123password` - **CHANGE IT IMMEDIATELY**
- ✅ SSH key authentication is configured
- ✅ Private network for internal cluster communication
- ✅ Firewall rules restrict access
- ⚠️ Consider using VPN for kubectl access to production clusters
