# Prometheus Basic Authentication Setup

This guide explains how to set up Basic Authentication for Prometheus following GitOps best practices.

## Prerequisites

- `htpasswd` command (from apache2-utils package)
- SOPS configured with age key
- Access to commit to the repository

## Step 1: Generate Password Hash

Generate a bcrypt hash for your desired username and password:

```bash
# Replace 'admin' and 'your-secure-password' with your desired credentials
htpasswd -nbs admin your-secure-password

# Example output:
# admin:$2y$05$QVc8K8zXJnF7xL.XmJ5g8.nZqJ5wU9vW4xK7vJ8U9vW4xK7vJ8U9v
```

## Step 2: Update the Secret File

Edit `apps/base/prometheus/auth-secret.yaml` and replace the placeholder hash:

```bash
# Open the file
vim apps/base/prometheus/auth-secret.yaml

# Replace this line:
#   users: admin:$2y$05$changeme_replace_with_real_hash

# With your generated hash:
#   users: admin:$2y$05$QVc8K8zXJnF7xL.XmJ5g8.nZqJ5wU9vW4xK7vJ8U9vW4xK7vJ8U9v
```

## Step 3: Encrypt with SOPS

Encrypt the secret file before committing:

```bash
sops --encrypt --in-place apps/base/prometheus/auth-secret.yaml

# Verify encryption
cat apps/base/prometheus/auth-secret.yaml | grep ENC
```

## Step 4: Commit and Deploy

```bash
# Add and commit
git add apps/base/prometheus/
git commit -m "Add Basic Authentication to Prometheus

- Add Traefik BasicAuth middleware
- Add SOPS-encrypted credentials secret
- Update ingress to require authentication"

# Push to trigger GitOps deployment
git push

# Trigger Flux reconciliation
flux reconcile kustomization apps --with-source
```

## Step 5: Verify Authentication

Test that authentication is working:

```bash
# This should return 401 Unauthorized
curl -I https://prometheus.k8s-demo.de

# This should return 200 OK (replace credentials)
curl -I -u admin:your-secure-password https://prometheus.k8s-demo.de
```

## Step 6: Update Grafana Datasource (if needed)

If Grafana needs to access Prometheus UI (it doesn't for queries via ClusterIP), update the datasource with credentials:

```bash
# Grafana queries Prometheus internally at:
# http://prometheus.prometheus.svc.cluster.local:9090
# This bypasses the ingress, so NO credentials needed!
```

## Quick Setup Script

```bash
#!/bin/bash
set -e

# Generate random password
PASSWORD=$(openssl rand -base64 16)
echo "Generated password: $PASSWORD"
echo "Save this password securely!"

# Generate hash
HASH=$(htpasswd -nbs admin "$PASSWORD")
echo "Generated hash: $HASH"

# Update secret file
sed -i "s|admin:\$2y\$.*|$HASH|" apps/base/prometheus/auth-secret.yaml

# Encrypt with SOPS
sops --encrypt --in-place apps/base/prometheus/auth-secret.yaml

echo "✓ Secret file updated and encrypted"
echo "✓ Username: admin"
echo "✓ Password: $PASSWORD"
echo ""
echo "Next steps:"
echo "1. git add apps/base/prometheus/auth-secret.yaml"
echo "2. git commit -m 'Configure Prometheus Basic Auth'"
echo "3. git push"
```

## Security Notes

- ✅ Credentials are SOPS-encrypted in git
- ✅ Traefik middleware handles authentication
- ✅ HTTPS enforced via Let's Encrypt
- ✅ Grafana accesses Prometheus internally (no auth needed)
- ⚠️ Store the password securely (password manager)
- ⚠️ Do NOT commit unencrypted credentials

## Troubleshooting

### Authentication not working

Check middleware is applied:
```bash
kubectl get middleware -n prometheus
kubectl describe ingress -n prometheus prometheus
```

### Wrong credentials

Check the secret:
```bash
kubectl get secret -n prometheus prometheus-basic-auth -o yaml
sops -d apps/base/prometheus/auth-secret.yaml
```

### Grafana can't access Prometheus

Grafana should use internal ClusterIP URL (no auth needed):
- URL: `http://prometheus.prometheus.svc.cluster.local:9090`
- This bypasses the ingress and authentication
