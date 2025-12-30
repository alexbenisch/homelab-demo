# DNS Management with Terraform

Manage DNS records for `k8s-demo.de` using Terraform and the Hetzner Cloud provider.

## Overview

This directory contains Terraform configuration to manage DNS zones and records using the new Hetzner Cloud DNS API. DNS changes can be applied via:

1. **GitHub Actions** (recommended) - Manage DNS through workflow UI
2. **Local Terraform** - Direct terraform commands for bulk changes

## Features

- ✅ Manage DNS zones and records as code
- ✅ Create/update/delete subdomains via GitHub Actions
- ✅ Automatic cluster IP detection
- ✅ Support for A, AAAA, CNAME, TXT, and MX records
- ✅ Version controlled DNS configuration
- ✅ State stored in repository

## Prerequisites

### Required Secrets

Configure in GitHub Settings → Secrets and variables → Actions:

| Secret Name | Description |
|-------------|-------------|
| `HCLOUD_TOKEN` | Hetzner Cloud API token with DNS permissions |

### DNS Zone Migration

If you're migrating from the old DNS API:

1. **Export existing records** from https://dns.hetzner.com
2. **Import zone** in Hetzner Cloud Console → DNS
3. **Import to Terraform** (see [Importing Existing Zone](#importing-existing-zone))

## Quick Start

### Create a Subdomain via GitHub Actions

1. Go to **Actions** → **DNS Management**
2. Click **Run workflow**
3. Configure:
   - **Action**: `apply`
   - **Subdomain**: `myapp` (creates myapp.k8s-demo.de)
   - **Record Type**: `A`
   - **Use cluster IP**: ✅ (auto-detects cluster IP)
   - **Comment**: `My application`
4. Click **Run workflow**

The workflow will:
- Detect your cluster's control plane IP
- Create/update the DNS record
- Commit the Terraform state

### Create Multiple Subdomains

For bulk operations, use local Terraform:

```bash
cd terraform/dns

# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit with your subdomains
nano terraform.tfvars

# Apply changes
export TF_VAR_hcloud_token="your-hetzner-cloud-token"
terraform init
terraform plan
terraform apply
```

## Usage Examples

### Example 1: Create A Record for New Application

```yaml
# Via GitHub Actions
Subdomain: myapp
Record Type: A
Record Value: (leave empty to use cluster IP)
Use cluster IP: ✅
Comment: My new application
```

Creates: `myapp.k8s-demo.de` → `<cluster-ip>`

### Example 2: Create CNAME Record

```yaml
# Via GitHub Actions
Subdomain: www
Record Type: CNAME
Record Value: k8s-demo.de.
Use cluster IP: ❌
Comment: WWW redirect
```

Creates: `www.k8s-demo.de` → `k8s-demo.de.`

### Example 3: Create TXT Record for Verification

```yaml
# Via GitHub Actions
Subdomain: _verification
Record Type: TXT
Record Value: verification-token-here
TTL: 300
Comment: Domain verification
```

Creates: `_verification.k8s-demo.de` → `"verification-token-here"`

### Example 4: Bulk Create All App Subdomains

Edit `terraform.tfvars`:

```hcl
zone_name   = "k8s-demo.de"
default_ttl = 3600
cluster_ip  = "your.cluster.ip.here"

subdomains = {
  "linkding" = {
    type    = "A"
    value   = "your.cluster.ip.here"
    comment = "Linkding bookmark manager"
  }

  "wordpress" = {
    type    = "A"
    value   = "your.cluster.ip.here"
    comment = "WordPress CMS"
  }

  "demo-django" = {
    type    = "A"
    value   = "your.cluster.ip.here"
    comment = "Demo Django app"
  }

  "grafana" = {
    type    = "A"
    value   = "your.cluster.ip.here"
    comment = "Grafana monitoring"
  }
}
```

Then apply:

```bash
terraform apply
```

## Terraform Configuration

### File Structure

```
terraform/dns/
├── versions.tf              # Provider configuration
├── variables.tf             # Input variables
├── main.tf                  # DNS zone and record configuration
├── outputs.tf               # Output values
├── terraform.tfvars.example # Example configuration
├── terraform.tfvars         # Your configuration (gitignored)
├── .gitignore              # Ignore sensitive files
└── README.md               # This file
```

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `hcloud_token` | Hetzner Cloud API token | - (required) |
| `zone_name` | DNS zone name | `k8s-demo.de` |
| `default_ttl` | Default TTL for records | `3600` |
| `cluster_ip` | Cluster control plane IP | `""` |
| `subdomains` | Map of subdomains | `{}` |

### Subdomain Configuration

Each subdomain in the `subdomains` map has:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Record type (A, AAAA, CNAME, TXT, MX) |
| `value` | string | Yes | Record value (IP, hostname, text) |
| `ttl` | number | No | TTL in seconds (uses default if not set) |
| `comment` | string | No | Comment for the record |

### Example Configuration

```hcl
subdomains = {
  # A record
  "api" = {
    type    = "A"
    value   = "203.0.113.10"
    ttl     = 3600
    comment = "API server"
  }

  # CNAME record
  "www" = {
    type    = "CNAME"
    value   = "k8s-demo.de."
    comment = "WWW redirect"
  }

  # TXT record
  "_dmarc" = {
    type    = "TXT"
    value   = "v=DMARC1; p=none"
    ttl     = 300
    comment = "DMARC policy"
  }
}
```

## GitHub Workflow

### Workflow Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `action` | Action to perform (plan/apply/destroy) | Yes | `plan` |
| `subdomain` | Subdomain name without domain | No | - |
| `record_type` | DNS record type | No | `A` |
| `record_value` | Record value | No | - |
| `ttl` | TTL in seconds | No | `3600` |
| `comment` | Record comment | No | Auto-generated |
| `use_cluster_ip` | Use cluster IP (A records only) | No | `true` |

### Workflow Features

- **Auto-detect cluster IP**: Reads from infrastructure Terraform state
- **Plan before apply**: Always review changes
- **State management**: Automatically commits state to repository
- **Summary output**: Shows DNS configuration after apply

### Workflow Examples

**Preview changes (plan):**
```yaml
Action: plan
Subdomain: newapp
Record Type: A
Use cluster IP: ✅
```

**Create record (apply):**
```yaml
Action: apply
Subdomain: newapp
Record Type: A
Use cluster IP: ✅
Comment: New application
```

**Delete record (destroy):**
```yaml
Action: destroy
Subdomain: oldapp
```

## Importing Existing Zone

If you already have a DNS zone in Hetzner Cloud Console:

```bash
# Get zone ID from Hetzner Console → DNS → k8s-demo.de
ZONE_ID="your-zone-id"

# Import to Terraform
cd terraform/dns
terraform import hcloud_zone.k8s_demo $ZONE_ID

# Verify
terraform plan
```

## Local Development

### Initialize

```bash
cd terraform/dns
export TF_VAR_hcloud_token="your-token"
terraform init
```

### Plan Changes

```bash
terraform plan
```

### Apply Changes

```bash
terraform apply
```

### View Current Configuration

```bash
# Show all outputs
terraform output

# Show DNS summary
terraform output dns_summary

# Show specific record
terraform output dns_records
```

### Destroy All Records

```bash
# ⚠️ This will delete the entire zone!
terraform destroy
```

## Integration with Infrastructure

The DNS workflow can automatically detect your cluster's IP address from the infrastructure Terraform state:

```bash
# In terraform/ directory
terraform output control_plane_ipv4
# Used by DNS workflow when "use_cluster_ip" is enabled
```

This means after deploying infrastructure, DNS records automatically point to the new cluster.

## Common Tasks

### Update All Subdomains to New IP

```bash
# Edit terraform.tfvars
cluster_ip = "new.cluster.ip.here"

# Update all records
terraform apply
```

### Lower TTL Before Migration

```bash
# Edit terraform.tfvars
default_ttl = 300  # 5 minutes

# Apply
terraform apply

# Wait 24 hours before migration
```

### Add New Application

**Option A: Via GitHub Actions**
1. Actions → DNS Management
2. Subdomain: `myapp`
3. Use cluster IP: ✅
4. Apply

**Option B: Via Terraform**
1. Edit `terraform.tfvars`
2. Add to `subdomains` map
3. Run `terraform apply`

### Verify DNS Records

```bash
# Check record creation
dig myapp.k8s-demo.de +short

# Check nameservers
dig k8s-demo.de NS +short

# Check all records
dig k8s-demo.de ANY +noall +answer
```

## Troubleshooting

### "Error: zone already exists"

The zone exists in Hetzner but not in Terraform state. Import it:

```bash
terraform import hcloud_zone.k8s_demo <zone-id>
```

### "Error: unauthorized"

Check `HCLOUD_TOKEN` secret has DNS permissions.

### "Records not updating"

1. Verify Terraform apply succeeded
2. Wait for DNS propagation (TTL duration)
3. Check: `dig subdomain.k8s-demo.de +short`

### "Cannot find cluster IP"

The workflow looks for `terraform/terraform.tfstate`. Ensure infrastructure is deployed first.

## Best Practices

1. **Use GitHub Actions for single record changes**
2. **Use local Terraform for bulk operations**
3. **Lower TTL before major changes** (300 seconds)
4. **Always run `terraform plan` first**
5. **Keep state file in git** (or use remote backend)
6. **Comment all records** for documentation
7. **Use cluster_ip variable** for consistency

## Migration from Old DNS API

See [Migration Strategy](../../docs/migration-strategy.md) for complete guide.

Quick steps:
1. Export records from old API
2. Import zone to Hetzner Cloud Console
3. Import zone to Terraform: `terraform import hcloud_zone.k8s_demo <zone-id>`
4. Create `terraform.tfvars` with all records
5. Run `terraform plan` to verify
6. Run `terraform apply`

## State Management

### Current Setup (Simple)

State is stored in `terraform.tfstate` and committed to git.

**Pros:**
- Simple to set up
- Works with GitHub Actions
- No additional services needed

**Cons:**
- State file in git (contains record values)
- No state locking
- Not ideal for teams

### Remote State (Advanced)

For production, consider remote state:

```hcl
# Add to versions.tf
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "dns/terraform.tfstate"
    region = "eu-central-1"
  }
}
```

## Security

- ✅ API token stored in GitHub Secrets
- ✅ State file can be encrypted at rest
- ⚠️ Record values visible in state file
- ⚠️ State file committed to repository

For sensitive DNS records, consider:
- Remote state backend with encryption
- Private repository
- Access controls on state storage

## Cost

Hetzner Cloud DNS:
- **Zones**: Free (up to 100 zones)
- **Records**: Free (up to 1000 records per zone)
- **Queries**: Free (20 million queries/month included)

**Total Cost**: €0/month for typical homelab usage

## Support

- **Hetzner Cloud DNS Docs**: https://docs.hetzner.com/dns-console/
- **Terraform Provider**: https://registry.terraform.io/providers/hetznercloud/hcloud/
- **Migration Guide**: [docs/migration-strategy.md](../../docs/migration-strategy.md)

## Next Steps

1. **Deploy infrastructure** (if not done): See [terraform/README.md](../README.md)
2. **Import existing DNS zone** (if migrating)
3. **Create terraform.tfvars** with your subdomains
4. **Test with terraform plan**
5. **Apply DNS configuration**
6. **Verify records**: `dig subdomain.k8s-demo.de`
7. **Update external-dns** to use new API: See [Migration Guide](../../docs/migration-strategy.md)
