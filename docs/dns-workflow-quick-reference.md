# DNS Workflow Quick Reference

Quick commands and examples for managing DNS with the GitHub Actions workflow.

## Quick Start

### Create Subdomain (Auto-detect Cluster IP)

1. **Actions** → **DNS Management** → **Run workflow**
2. Settings:
   ```
   Action: apply
   Subdomain: myapp
   Record Type: A
   Use cluster IP: ✅
   ```
3. Done! Creates `myapp.k8s-demo.de` → cluster IP

## Common Tasks

### Create A Record for Application

```yaml
Action: apply
Subdomain: linkding
Record Type: A
Use cluster IP: ✅
Comment: Linkding bookmark manager
```

Result: `linkding.k8s-demo.de` → `<cluster-ip>`

### Create CNAME Record

```yaml
Action: apply
Subdomain: www
Record Type: CNAME
Record Value: k8s-demo.de.
Use cluster IP: ❌
Comment: WWW redirect
```

Result: `www.k8s-demo.de` → `k8s-demo.de.`

### Create TXT Record

```yaml
Action: apply
Subdomain: _verification
Record Type: TXT
Record Value: verification-token-here
TTL: 300
Comment: Domain verification
```

Result: `_verification.k8s-demo.de` TXT `"verification-token-here"`

### Create A Record with Custom IP

```yaml
Action: apply
Subdomain: external
Record Type: A
Record Value: 203.0.113.10
Use cluster IP: ❌
Comment: External service
```

Result: `external.k8s-demo.de` → `203.0.113.10`

### Preview Changes (Plan)

```yaml
Action: plan
Subdomain: newapp
Record Type: A
Use cluster IP: ✅
```

Shows what will change without applying.

### Delete Subdomain

```yaml
Action: destroy
Subdomain: oldapp
```

Removes `oldapp.k8s-demo.de` from DNS.

## Verification

After creating a record, verify:

```bash
# Check DNS resolution
dig myapp.k8s-demo.de +short

# Test HTTPS (after cert issued)
curl -I https://myapp.k8s-demo.de

# Check propagation
dig myapp.k8s-demo.de @8.8.8.8 +short
```

## Bulk Operations

For creating many subdomains at once, use Terraform directly:

```bash
cd terraform/dns

# Create config
cat > terraform.tfvars <<EOF
zone_name = "k8s-demo.de"
cluster_ip = "your.cluster.ip"

subdomains = {
  "app1" = { type = "A", value = "your.cluster.ip", comment = "App 1" }
  "app2" = { type = "A", value = "your.cluster.ip", comment = "App 2" }
  "app3" = { type = "A", value = "your.cluster.ip", comment = "App 3" }
}
EOF

# Apply
terraform init
terraform apply
```

## Troubleshooting

### Record Not Resolving

```bash
# Wait for propagation (usually < 5 min)
# Check with dig
dig subdomain.k8s-demo.de +short

# Check nameservers
dig k8s-demo.de NS +short
```

### Workflow Failed

1. Check GitHub Actions logs
2. Common issues:
   - `HCLOUD_TOKEN` not set
   - Zone doesn't exist (import first)
   - Invalid record value

### Import Existing Zone

```bash
cd terraform/dns
terraform import hcloud_zone.k8s_demo <zone-id-from-hetzner-console>
```

## Tips

- ✅ Use **Plan** before **Apply** to preview changes
- ✅ Enable "Use cluster IP" for application subdomains
- ✅ Add meaningful comments to all records
- ✅ Use low TTL (300) before major changes
- ✅ Verify with `dig` after creating records

## Full Documentation

- **Complete Guide**: [terraform/dns/README.md](../terraform/dns/README.md)
- **Terraform Setup**: [terraform/README.md](../terraform/README.md)
- **Migration Guide**: [migration-strategy.md](migration-strategy.md)

## Examples by Record Type

### A Record (IPv4)
```yaml
Subdomain: api
Record Type: A
Record Value: 203.0.113.10
```

### AAAA Record (IPv6)
```yaml
Subdomain: api
Record Type: AAAA
Record Value: 2001:db8::1
```

### CNAME Record
```yaml
Subdomain: blog
Record Type: CNAME
Record Value: hosting-provider.com.
```

### TXT Record
```yaml
Subdomain: _dmarc
Record Type: TXT
Record Value: v=DMARC1; p=none
```

### MX Record
```yaml
Subdomain: @
Record Type: MX
Record Value: 10 mail.example.com.
```

## Workflow Inputs Reference

| Field | Description | Example |
|-------|-------------|---------|
| Action | `plan`, `apply`, or `destroy` | `apply` |
| Subdomain | Name without domain | `myapp` |
| Record Type | A, AAAA, CNAME, TXT, MX | `A` |
| Record Value | IP, hostname, or text | `203.0.113.10` |
| TTL | Seconds (optional) | `3600` |
| Comment | Description (optional) | `My app` |
| Use cluster IP | Auto-detect cluster IP | `✅` |

## Next Steps

1. Try creating a test subdomain
2. Verify it resolves: `dig test.k8s-demo.de`
3. Deploy application with that subdomain
4. Access via HTTPS (after cert-manager)

Need more help? See [terraform/dns/README.md](../terraform/dns/README.md)
