# Terraform Deployment for Homelab K3s Cluster

This directory contains Terraform configuration to automatically provision a k3s cluster on Hetzner Cloud using GitHub Actions workflows.

> **📋 Migrating from existing cluster?** See the [Migration Strategy Guide](../docs/migration-strategy.md) for a complete step-by-step migration plan including DNS API migration.

## Features

- **Automated Infrastructure**: Provision entire k3s cluster with one click
- **GitHub Actions Integration**: Deploy, plan, or destroy via GitHub UI
- **Version Controlled**: Infrastructure as Code in git
- **Cost Effective**: ~€13.50/month for 3-node cluster

## Architecture

The Terraform configuration creates:

- **Network**: Private network (`10.0.0.0/16`) for secure internal communication
- **Firewall**: Rules for SSH (22), HTTP (80), HTTPS (443), and Kubernetes API (6443)
- **Control Plane** (`ctrl`): k3s server node at `10.0.1.10`
- **Worker 1** (`wrkr1`): k3s agent node at `10.0.1.20`
- **Worker 2** (`wrkr2`): k3s agent node at `10.0.1.21`

All nodes run on Hetzner CPX11 instances (2 vCPU, 2 GB RAM) in Nuremberg (nbg1).

## Prerequisites

### 1. Hetzner Cloud Account

Create an account at https://www.hetzner.com/cloud

### 2. GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `HCLOUD_TOKEN` | Hetzner Cloud API token | `your-hetzner-api-token` |
| `USER_PASSWORD` | Password for alex user | `SecurePassword123!` |

**To create Hetzner API token:**
1. Log into Hetzner Cloud Console
2. Go to your project → Security → API Tokens
3. Click "Generate API Token"
4. Give it "Read & Write" permissions
5. Copy the token and add it to GitHub secrets

## Usage

### Deploy Infrastructure

1. Go to **Actions** tab in your GitHub repository
2. Select **Terraform Deployment** workflow
3. Click **Run workflow**
4. Choose:
   - **Action**: `apply`
   - **Auto-approve**: Check this to skip confirmation
5. Click **Run workflow**

The workflow will:
- Initialize Terraform
- Create network, firewall, and servers
- Configure k3s on all nodes
- Output server IPs and next steps

**Duration**: ~3-5 minutes

### View Planned Changes

To see what Terraform will do without making changes:

1. Go to **Actions** → **Terraform Deployment**
2. Choose **Action**: `plan`
3. Run workflow
4. Review the plan output in the workflow logs

### Destroy Infrastructure

To delete all resources and stop billing:

1. Go to **Actions** → **Terraform Deployment**
2. Choose:
   - **Action**: `destroy`
   - **Auto-approve**: Check this to skip confirmation
3. Run workflow

**Warning**: This will permanently delete all servers and data!

## Post-Deployment Steps

After successful deployment:

### 1. Wait for Cloud-Init

Allow 2-3 minutes for cloud-init to complete on all servers. You can monitor progress by SSHing into the servers.

### 2. Get Server IPs

Find the output in the workflow run or check Hetzner Cloud Console. The workflow outputs:
- Control plane public IP
- Worker 1 public IP
- Worker 2 public IP

### 3. Connect to Control Plane

```bash
# SSH into control plane (password from USER_PASSWORD secret)
ssh alex@<CONTROL_PLANE_IP>

# Check k3s status
sudo systemctl status k3s
kubectl get nodes

# Get k3s token for workers
sudo cat /var/lib/rancher/k3s/server/node-token
```

### 4. Configure Workers

Workers need the k3s token from the control plane:

```bash
# SSH into worker 1
ssh alex@<WORKER1_IP>

# Edit the agent installation script
sudo nano /root/install-k3s-agent.sh

# Replace <K3S_TOKEN_FROM_CONTROL_PLANE> with actual token
# Save and exit (Ctrl+X, Y, Enter)

# Run the installation
sudo /root/install-k3s-agent.sh
```

Repeat for worker 2.

### 5. Verify Cluster

Back on the control plane:

```bash
kubectl get nodes

# Expected output:
# NAME     STATUS   ROLES                  AGE   VERSION
# ctrl     Ready    control-plane,master   5m    v1.28.x+k3s1
# wrkr1    Ready    <none>                 2m    v1.28.x+k3s1
# wrkr2    Ready    <none>                 2m    v1.28.x+k3s1
```

### 6. Get Kubeconfig

Copy kubeconfig to your local machine:

```bash
# On your local machine
scp alex@<CONTROL_PLANE_IP>:/home/alex/.kube/config ~/.kube/config

# Update server address to use public IP
sed -i 's/127.0.0.1/<CONTROL_PLANE_IP>/g' ~/.kube/config

# Test connection
kubectl get nodes
```

## Local Development

To test Terraform locally before using GitHub Actions:

```bash
cd terraform

# Set environment variables
export TF_VAR_hcloud_token="your-token"
export TF_VAR_user_password="your-password"

# Initialize
terraform init

# Plan changes
terraform plan

# Apply (create infrastructure)
terraform apply

# Destroy (delete infrastructure)
terraform destroy
```

## File Structure

```
terraform/
├── versions.tf           # Terraform and provider versions
├── variables.tf          # Input variables
├── main.tf              # Main infrastructure configuration
├── outputs.tf           # Output values (IPs, commands)
├── cloud-init/          # Cloud-init templates
│   ├── control-plane.tftpl
│   └── worker.tftpl
└── README.md            # This file
```

## State Management

Terraform state is stored in the repository at `terraform/terraform.tfstate`.

**Important:**
- State file is committed after `apply` and `destroy` operations
- **Do not** manually edit the state file
- For production, consider using remote state (S3, Terraform Cloud)

## Customization

### Change Server Type

Edit `terraform/variables.tf`:

```hcl
variable "server_type" {
  default = "cpx21"  # 3 vCPU, 4 GB RAM
}
```

### Change Location

```hcl
variable "location" {
  default = "fsn1"  # Falkenstein
}
```

### Change Network Range

```hcl
variable "network_ip_range" {
  default = "172.16.0.0/16"
}
```

## Troubleshooting

### Workflow Fails with "API token invalid"

- Verify `HCLOUD_TOKEN` secret is set correctly
- Generate a new API token in Hetzner Cloud Console
- Ensure token has "Read & Write" permissions

### Workers Not Joining Cluster

1. SSH into control plane and get token:
   ```bash
   sudo cat /var/lib/rancher/k3s/server/node-token
   ```

2. SSH into worker and check installation script:
   ```bash
   cat /root/install-k3s-agent.sh
   ```

3. Verify network connectivity:
   ```bash
   ping 10.0.1.10
   curl -k https://10.0.1.10:6443
   ```

### Cloud-Init Not Completing

```bash
# Check cloud-init status
sudo cloud-init status --long

# View logs
sudo tail -f /var/log/cloud-init-output.log
```

### State Lock Error

If state is locked:

```bash
cd terraform
terraform force-unlock <lock-id>
```

## Cost Estimate

- **3x CPX11 servers**: €4.50/month each = €13.50/month
- **Network**: Free
- **Traffic**: 20 TB included per server
- **Snapshots** (if created): €0.0119/GB/month

**Total**: ~€13.50/month

## Security Considerations

- Change default password immediately after first login
- SSH key authentication is enabled by default
- Private network for internal cluster communication
- Firewall restricts access to necessary ports only
- Consider using a VPN for kubectl access in production
- Rotate API tokens regularly

## Migration from Manual Cloud-Init

If you previously used manual cloud-init setup:

1. Destroy old servers manually in Hetzner Console
2. Run Terraform deployment workflow
3. Update DNS records with new IPs
4. Redeploy applications to new cluster

## DNS Management

After deploying infrastructure, manage your DNS records:

**Via GitHub Actions (recommended for single subdomains):**
1. Go to **Actions** → **DNS Management**
2. Create subdomain: `myapp` → automatically points to cluster IP
3. See [DNS Management Guide](dns/README.md)

**Via Terraform (for bulk operations):**
```bash
cd terraform/dns
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with all your subdomains
terraform apply
```

Full documentation: [terraform/dns/README.md](dns/README.md)

## Next Steps

After cluster is running:

1. **Manage DNS**: Use [DNS Management Workflow](dns/README.md) to create subdomains
2. **Deploy Ingress Controller**: `kubectl apply -f kubernetes/infrastructure/ingress-nginx/`
3. **Setup Cert-Manager**: Follow `kubernetes/infrastructure/cert-manager/README.md`
4. **Deploy Applications**: `kubectl apply -f kubernetes/apps/`

## Support

For issues:
- Check workflow logs in GitHub Actions
- Review Terraform output for error messages
- SSH into servers and check cloud-init logs
- Verify Hetzner Cloud Console for resource status
