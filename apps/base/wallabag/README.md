# Wallabag - Tailnet-Only Deployment

Wallabag is a self-hosted read-it-later application. This deployment is configured to be accessible only on your Tailnet via Tailscale sidecar.

## Access

- **URL**: `https://wallabag.tail55277.ts.net`
- **Network**: Tailnet only (not publicly accessible)
- **TLS**: Automatic via Tailscale MagicDNS

## Prerequisites

1. Tailscale account with MagicDNS enabled
2. Tailscale auth key (generate at: https://login.tailscale.com/admin/settings/keys)
   - Set as **Reusable**: Yes
   - Set as **Ephemeral**: No
   - Optional tag: `tag:k8s`

## Deployment Steps

### 1. Update Tailscale Auth Key

Edit the secret with your actual Tailscale auth key:

```bash
# Edit the secret file
vim apps/base/wallabag/secret.yaml

# Replace REPLACE_WITH_YOUR_TAILSCALE_AUTH_KEY with your actual key
# Example: tskey-auth-xxxxxxxxxxxxx
```

### 2. Encrypt the Secret with SOPS

```bash
sops -e -i apps/base/wallabag/secret.yaml
```

### 3. Commit and Push

```bash
git add apps/base/wallabag apps/staging/wallabag apps/staging/kustomization.yaml
git commit -m "Add wallabag with Tailscale sidecar for Tailnet-only access"
git push
```

### 4. Reconcile Flux

```bash
flux reconcile kustomization apps --with-source
```

### 5. Verify Deployment

```bash
# Check pod status
kubectl get pods -n wallabag

# Check Tailscale sidecar logs
kubectl logs -n wallabag -l app=wallabag -c tailscale

# Check wallabag logs
kubectl logs -n wallabag -l app=wallabag -c wallabag

# Verify PVC
kubectl get pvc -n wallabag
```

### 6. Check Tailscale Status

From any device on your Tailnet:

```bash
tailscale status
```

You should see `wallabag` listed as a device.

### 7. Access Wallabag

Open your browser and navigate to:
```
https://wallabag.tail55277.ts.net
```

**Default credentials:**
- Username: `wallabag`
- Password: `wallabag`

**Important:** Change these credentials immediately after first login!

## Configuration

### Environment Variables

Key environment variables in `deployment.yaml`:

- `SYMFONY__ENV__DOMAIN_NAME`: The HTTPS URL for Wallabag (set to Tailnet URL)
- `SYMFONY__ENV__FOSUSER_REGISTRATION`: Disabled (false) - prevents public registration
- `SYMFONY__ENV__FOSUSER_CONFIRMATION`: Disabled (false)

### Storage

- **Data volume**: `/var/www/wallabag/data` (5Gi PVC)
- **Images**: `/var/www/wallabag/web/assets/images` (emptyDir)

### Tailscale Configuration

The `tailscale-config.yaml` ConfigMap defines how Tailscale serves the application:

- **Port 443**: HTTPS enabled via Tailscale
- **Proxy**: Forwards to wallabag container on `http://127.0.0.1:80`

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -n wallabag -l app=wallabag

# Check wallabag container logs
kubectl logs -n wallabag -l app=wallabag -c wallabag

# Check Tailscale sidecar logs
kubectl logs -n wallabag -l app=wallabag -c tailscale
```

### Tailscale Not Connecting

Common issues:
- Invalid or expired auth key
- Auth key not properly encrypted with SOPS
- Network policies blocking Tailscale

Check Tailscale logs:
```bash
kubectl logs -n wallabag -l app=wallabag -c tailscale --tail=50
```

### Can't Access via Tailnet

1. Verify MagicDNS is enabled in Tailscale admin console
2. Check that the pod is running: `kubectl get pods -n wallabag`
3. Verify Tailscale device is online: `tailscale status`
4. Try accessing via Tailnet IP instead of hostname

### Permission Errors

The wallabag container runs as user `65534` (nobody). If you see permission errors:

```bash
kubectl exec -n wallabag -l app=wallabag -c wallabag -- ls -la /var/www/wallabag/data
```

## Security Notes

1. **Tailnet-only access**: This deployment has NO ingress configured, so it's only accessible via Tailnet
2. **Change default credentials**: The default wallabag/wallabag credentials should be changed immediately
3. **Auth key security**: The Tailscale auth key is encrypted with SOPS - never commit it unencrypted
4. **Registration disabled**: Public registration is disabled to prevent unauthorized access

## Upgrading

To upgrade Wallabag:

```bash
# Edit deployment.yaml and update the image tag
vim apps/base/wallabag/deployment.yaml

# Change: image: wallabag/wallabag:latest
# To:     image: wallabag/wallabag:2.6.9  # or desired version

# Commit and push
git add apps/base/wallabag/deployment.yaml
git commit -m "Upgrade wallabag to version X.Y.Z"
git push

# Reconcile
flux reconcile kustomization apps --with-source
```

## Backup

To backup Wallabag data:

```bash
# Create backup of PVC data
kubectl exec -n wallabag -l app=wallabag -c wallabag -- tar czf - /var/www/wallabag/data > wallabag-backup-$(date +%Y%m%d).tar.gz
```

## Resources

- [Wallabag Documentation](https://doc.wallabag.org/)
- [Wallabag Docker Image](https://hub.docker.com/r/wallabag/wallabag)
- [Tailscale Serve Documentation](https://tailscale.com/kb/1242/tailscale-serve/)
