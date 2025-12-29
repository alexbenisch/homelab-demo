# Migration Strategy: Old Cluster → New Cluster + New Hetzner DNS API

This document outlines the complete migration strategy from the current cluster to a new Terraform-managed cluster with the new Hetzner DNS API.

## Table of Contents

1. [Overview](#overview)
2. [Migration Challenges](#migration-challenges)
3. [Prerequisites](#prerequisites)
4. [Migration Phases](#migration-phases)
5. [Detailed Steps](#detailed-steps)
6. [Rollback Plan](#rollback-plan)
7. [Post-Migration](#post-migration)

## Overview

### Current State
- k3s cluster (manual setup via cloud-init)
- External-DNS using Hetzner DNS webhook with **legacy DNS API**
- DNS zone `k8s-demo.de` managed via old API (dns.hetzner.com)
- Multiple applications deployed via Flux

### Target State
- k3s cluster (Terraform-managed via GitHub Actions)
- External-DNS using Hetzner DNS webhook with **new Cloud DNS API**
- DNS zone `k8s-demo.de` managed via new API (Hetzner Console)
- All applications migrated with minimal downtime

### Key Constraint
**Once you migrate the DNS zone to the new API, you cannot manage subdomains via the old API anymore.**

## Migration Challenges

1. **DNS API Migration**: Zone migration is one-way; no reverting to old API
2. **DNS Propagation**: Changes may take minutes to propagate
3. **Application Downtime**: Need to minimize service interruption
4. **State Transfer**: PersistentVolumes need to be backed up and restored
5. **Secrets Management**: SOPS-encrypted secrets need to work on new cluster

## Prerequisites

### Before Starting

- [ ] **Backup everything**:
  - [ ] Export all PersistentVolume data (linkding, wallabag, wordpress, grafana)
  - [ ] Save kubeconfig from current cluster
  - [ ] Export all Kubernetes secrets: `kubectl get secrets --all-namespaces -o yaml > secrets-backup.yaml`
  - [ ] Document all DNS records: `dig k8s-demo.de ANY` and all subdomains
  - [ ] Backup SOPS age key: `~/.config/sops/age/keys.txt`

- [ ] **Hetzner Account Setup**:
  - [ ] Hetzner Cloud API token created (for Terraform)
  - [ ] Hetzner Cloud API token created (for new DNS API)
  - [ ] Review current DNS zone records at https://dns.hetzner.com

- [ ] **GitHub Setup**:
  - [ ] Fork/clone repository
  - [ ] GitHub secrets configured (`HCLOUD_TOKEN`, `USER_PASSWORD`)
  - [ ] Test Terraform workflow with `plan` action

- [ ] **Communication**:
  - [ ] Notify users of planned maintenance window
  - [ ] Schedule migration during low-traffic period

## Migration Phases

### Phase 1: Preparation (No Downtime)
**Duration**: 1-2 hours
**Risk**: Low

1. Create backups of all data
2. Deploy new cluster via Terraform
3. Install Flux and infrastructure on new cluster
4. Test applications on new cluster (without DNS)
5. Verify everything works via IP addresses

### Phase 2: DNS Migration (Brief Downtime)
**Duration**: 15-30 minutes
**Risk**: Medium-High

1. Lower TTL on all DNS records (do this 24h before if possible)
2. Migrate DNS zone to new Hetzner API
3. Update DNS records to point to new cluster
4. Wait for propagation
5. Verify all services accessible

### Phase 3: Cleanup (No Downtime)
**Duration**: 30 minutes
**Risk**: Low

1. Monitor new cluster for 24-48 hours
2. Decommission old cluster
3. Remove old infrastructure

## Detailed Steps

### Step 1: Backup Current Cluster

Create comprehensive backups:

```bash
# Create backup directory
mkdir -p ~/homelab-migration-backup
cd ~/homelab-migration-backup

# Export all resources
kubectl get all --all-namespaces -o yaml > all-resources.yaml
kubectl get pv,pvc --all-namespaces -o yaml > volumes.yaml
kubectl get ingress --all-namespaces -o yaml > ingress.yaml
kubectl get secrets --all-namespaces -o yaml > secrets.yaml
kubectl get configmap --all-namespaces -o yaml > configmaps.yaml

# Backup PersistentVolume data
# Linkding
kubectl exec -n linkding $(kubectl get pod -n linkding -l app=linkding -o jsonpath='{.items[0].metadata.name}') -- tar czf - /etc/linkding > linkding-data.tar.gz

# Wallabag
kubectl exec -n wallabag $(kubectl get pod -n wallabag -l app=wallabag -o jsonpath='{.items[0].metadata.name}') -- tar czf - /var/www/wallabag/data > wallabag-data.tar.gz

# WordPress
kubectl exec -n wordpress $(kubectl get pod -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}') -- tar czf - /var/www/html > wordpress-data.tar.gz

# WordPress MySQL
kubectl exec -n wordpress $(kubectl get pod -n wordpress -l app=mysql -o jsonpath='{.items[0].metadata.name}') -- mysqldump -u root -p$(kubectl get secret -n wordpress mysql-secret -o jsonpath='{.data.mysql-root-password}' | base64 -d) --all-databases > wordpress-mysql-backup.sql

# Grafana
kubectl exec -n grafana $(kubectl get pod -n grafana -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -- tar czf - /var/lib/grafana > grafana-data.tar.gz

# Save current DNS records
echo "Current DNS records for k8s-demo.de:"
dig k8s-demo.de ANY +noall +answer > dns-records-before.txt
dig linkding.k8s-demo.de +short >> dns-records-before.txt
dig wordpress.k8s-demo.de +short >> dns-records-before.txt
dig demo-django.k8s-demo.de +short >> dns-records-before.txt
dig demo-api.k8s-demo.de +short >> dns-records-before.txt
dig grafana.k8s-demo.de +short >> dns-records-before.txt
dig tested-django.k8s-demo.de +short >> dns-records-before.txt

# Backup SOPS key
cp ~/.config/sops/age/keys.txt ~/homelab-migration-backup/sops-age-key.txt

echo "Backup complete! Files in ~/homelab-migration-backup/"
```

### Step 2: Deploy New Cluster with Terraform

```bash
# Navigate to repository
cd ~/repos/homelab-demo

# Option A: Deploy via GitHub Actions (recommended)
# 1. Go to GitHub Actions → Terraform Deployment
# 2. Run workflow with action: "apply"
# 3. Wait for completion (~5 minutes)

# Option B: Deploy locally
cd terraform
export TF_VAR_hcloud_token="your-hetzner-cloud-token"
export TF_VAR_user_password="SecurePassword123"
terraform init
terraform plan
terraform apply

# Save outputs
terraform output > ../new-cluster-info.txt
cd ..
```

### Step 3: Configure New Cluster

Wait for cloud-init to complete (2-3 minutes), then:

```bash
# Get control plane IP from Terraform output
NEW_CTRL_IP=$(grep "control_plane_ipv4" new-cluster-info.txt | awk '{print $3}' | tr -d '"')

# SSH to control plane
ssh alex@$NEW_CTRL_IP

# Get k3s token
sudo cat /var/lib/rancher/k3s/server/node-token
# Copy this token

# Exit control plane
exit

# SSH to worker1 and configure
NEW_WORKER1_IP=$(grep "worker1_ipv4" new-cluster-info.txt | awk '{print $3}' | tr -d '"')
ssh alex@$NEW_WORKER1_IP
sudo nano /root/install-k3s-agent.sh
# Replace <K3S_TOKEN_FROM_CONTROL_PLANE> with actual token
sudo /root/install-k3s-agent.sh
exit

# SSH to worker2 and configure
NEW_WORKER2_IP=$(grep "worker2_ipv4" new-cluster-info.txt | awk '{print $3}' | tr -d '"')
ssh alex@$NEW_WORKER2_IP
sudo nano /root/install-k3s-agent.sh
# Replace <K3S_TOKEN_FROM_CONTROL_PLANE> with actual token
sudo /root/install-k3s-agent.sh
exit

# Get kubeconfig from new cluster
scp alex@$NEW_CTRL_IP:/home/alex/.kube/config ~/.kube/config-new
export KUBECONFIG=~/.kube/config-new
sed -i "s/127.0.0.1/$NEW_CTRL_IP/g" ~/.kube/config-new

# Verify new cluster
kubectl get nodes
# Should show: ctrl, wrkr1, wrkr2 all Ready
```

### Step 4: Update External-DNS for New API

Create updated external-dns configuration:

```bash
# Update the external-dns release to use new Cloud API
cat > infrastructure/base/external-dns/release-new-api.yaml <<'EOF'
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: external-dns
  namespace: kube-system
spec:
  interval: 10m
  chart:
    spec:
      chart: external-dns
      version: 1.15.0
      sourceRef:
        kind: HelmRepository
        name: external-dns
        namespace: kube-system
      interval: 12h
  values:
    provider:
      name: webhook
      webhook:
        image:
          repository: ghcr.io/mconfalonieri/external-dns-hetzner-webhook
          tag: v0.7.0
        env:
          - name: HETZNER_API_KEY
            valueFrom:
              secretKeyRef:
                name: hetzner-dns-api
                key: HOMELAB_HETZNER_DNS_API_KEY
          - name: USE_CLOUD_API
            value: "true"
          - name: LOG_LEVEL
            value: debug
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8080
          initialDelaySeconds: 10
          timeoutSeconds: 5
    domainFilters:
      - "k8s-demo.de"
    policy: upsert-only
    txtOwnerId: "homelab-new"
    sources:
      - ingress
    interval: 2m
EOF

# Note: txtOwnerId changed to "homelab-new" to avoid conflicts during migration
```

Create new secret with Cloud API token:

```bash
# Create new secret (unencrypted first)
cat > infrastructure/base/external-dns/secret-new-api.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: hetzner-dns-api
  namespace: kube-system
type: Opaque
stringData:
  HOMELAB_HETZNER_DNS_API_KEY: YOUR_NEW_CLOUD_API_TOKEN_HERE
EOF

# Encrypt with SOPS
sops --encrypt --in-place infrastructure/base/external-dns/secret-new-api.yaml

# Verify encryption
cat infrastructure/base/external-dns/secret-new-api.yaml | grep ENC
```

### Step 5: Install Flux on New Cluster

```bash
# Switch to new cluster context
export KUBECONFIG=~/.kube/config-new

# Install Flux (if not already present in Terraform output)
flux check --pre
flux install

# Create SOPS secret for Flux to decrypt secrets
# Use the same age key as old cluster
cat ~/.config/sops/age/keys.txt | kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey=/dev/stdin

# Bootstrap Flux from your repository
flux create source git homelab-demo \
  --url=https://github.com/YOUR_USERNAME/homelab-demo \
  --branch=main \
  --interval=1m

# Apply infrastructure kustomization
flux create kustomization infrastructure \
  --source=homelab-demo \
  --path=./infrastructure/staging \
  --prune=true \
  --interval=10m \
  --decryption-provider=sops \
  --decryption-secret=sops-age

# Apply apps kustomization
flux create kustomization apps \
  --source=homelab-demo \
  --path=./apps/staging \
  --prune=true \
  --interval=10m \
  --depends-on=infrastructure \
  --decryption-provider=sops \
  --decryption-secret=sops-age

# Watch deployment
flux get kustomizations --watch
```

### Step 6: Restore Application Data

Before changing DNS, restore data to new cluster:

```bash
# Linkding
kubectl exec -n linkding $(kubectl get pod -n linkding -l app=linkding -o jsonpath='{.items[0].metadata.name}') -- tar xzf - -C / < ~/homelab-migration-backup/linkding-data.tar.gz

# Wallabag
kubectl exec -n wallabag $(kubectl get pod -n wallabag -l app=wallabag -o jsonpath='{.items[0].metadata.name}') -- tar xzf - -C / < ~/homelab-migration-backup/wallabag-data.tar.gz

# WordPress files
kubectl exec -n wordpress $(kubectl get pod -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}') -- tar xzf - -C / < ~/homelab-migration-backup/wordpress-data.tar.gz

# WordPress database
kubectl cp ~/homelab-migration-backup/wordpress-mysql-backup.sql wordpress/$(kubectl get pod -n wordpress -l app=mysql -o jsonpath='{.items[0].metadata.name}'):/tmp/backup.sql
kubectl exec -n wordpress $(kubectl get pod -n wordpress -l app=mysql -o jsonpath='{.items[0].metadata.name}') -- mysql -u root -p$(kubectl get secret -n wordpress mysql-secret -o jsonpath='{.data.mysql-root-password}' | base64 -d) < /tmp/backup.sql

# Grafana
kubectl exec -n grafana $(kubectl get pod -n grafana -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -- tar xzf - -C / < ~/homelab-migration-backup/grafana-data.tar.gz

# Restart pods to pick up restored data
kubectl rollout restart deployment -n linkding
kubectl rollout restart deployment -n wallabag
kubectl rollout restart deployment -n wordpress
kubectl rollout restart deployment -n grafana
```

### Step 7: Test New Cluster (Without DNS)

Test applications via IP before switching DNS:

```bash
# Get new control plane IP
NEW_CTRL_IP=$(grep "control_plane_ipv4" new-cluster-info.txt | awk '{print $3}' | tr -d '"')

# Test each application by adding Host header
# Linkding
curl -H "Host: linkding.k8s-demo.de" http://$NEW_CTRL_IP

# WordPress
curl -H "Host: wordpress.k8s-demo.de" http://$NEW_CTRL_IP

# Demo Django
curl -H "Host: demo-django.k8s-demo.de" http://$NEW_CTRL_IP

# Demo API
curl -H "Host: demo-api.k8s-demo.de" http://$NEW_CTRL_IP/health

# Grafana
curl -H "Host: grafana.k8s-demo.de" http://$NEW_CTRL_IP

# Tested Django
curl -H "Host: tested-django.k8s-demo.de" http://$NEW_CTRL_IP

# Or add to /etc/hosts for browser testing
echo "$NEW_CTRL_IP linkding.k8s-demo.de wordpress.k8s-demo.de demo-django.k8s-demo.de demo-api.k8s-demo.de grafana.k8s-demo.de tested-django.k8s-demo.de" | sudo tee -a /etc/hosts

# Test in browser, then remove when done:
sudo sed -i '/$NEW_CTRL_IP/d' /etc/hosts
```

### Step 8: Lower DNS TTL (24 Hours Before Migration)

**Do this at least 24 hours before DNS migration:**

```bash
# Log into https://dns.hetzner.com
# For each record:
# 1. Find the record
# 2. Edit TTL to 300 (5 minutes)
# 3. Save

# This ensures quick propagation when you update records later
```

### Step 9: Migrate DNS Zone to New API

**⚠️ POINT OF NO RETURN: After this step, you cannot use the old API anymore**

1. **Export DNS Zone from Old API**:
   ```bash
   # Document all records before migration
   dig k8s-demo.de ANY +noall +answer > dns-records-export.txt

   # Manually list all subdomains and their IPs
   echo "Current DNS records:" > dns-migration-plan.txt
   kubectl get ingress --all-namespaces -o custom-columns=HOST:.spec.rules[0].host,IP:.status.loadBalancer.ingress[0].ip >> dns-migration-plan.txt
   ```

2. **Migrate Zone in Hetzner Console**:
   - Log into https://console.hetzner.cloud
   - Go to **DNS** section (not the old dns.hetzner.com)
   - Click **Import Zone** or **Add Zone**
   - Import `k8s-demo.de`
   - Verify all records are present

3. **Update DNS Records to Point to New Cluster**:

   **Option A: Manual Update** (immediate):
   ```bash
   # In Hetzner Cloud Console DNS tab:
   # Update each A record to point to new control plane IP
   #
   # linkding.k8s-demo.de → NEW_CTRL_IP
   # wordpress.k8s-demo.de → NEW_CTRL_IP
   # demo-django.k8s-demo.de → NEW_CTRL_IP
   # demo-api.k8s-demo.de → NEW_CTRL_IP
   # grafana.k8s-demo.de → NEW_CTRL_IP
   # tested-django.k8s-demo.de → NEW_CTRL_IP
   ```

   **Option B: Let External-DNS Create Records** (slower but automated):
   - Update external-dns secret with Cloud API token
   - Replace `infrastructure/base/external-dns/release.yaml` with `release-new-api.yaml`
   - Replace `infrastructure/base/external-dns/secret.yaml` with `secret-new-api.yaml`
   - Commit and push
   - Wait for Flux to reconcile
   - Wait for external-dns to create records (~2 minutes)

4. **Verify DNS Propagation**:
   ```bash
   # Check DNS resolution
   dig linkding.k8s-demo.de +short
   # Should return NEW_CTRL_IP

   dig wordpress.k8s-demo.de +short
   # Should return NEW_CTRL_IP

   # Test with actual requests
   curl https://linkding.k8s-demo.de
   curl https://wordpress.k8s-demo.de
   curl https://demo-api.k8s-demo.de/health
   ```

### Step 10: Monitor and Verify

```bash
# Switch to new cluster permanently
cp ~/.kube/config-new ~/.kube/config

# Monitor all pods
kubectl get pods --all-namespaces --watch

# Check external-dns logs
kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns -f

# Check ingress controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik -f

# Check certificate issuance
kubectl get certificate --all-namespaces

# Monitor for 24-48 hours
watch kubectl get pods --all-namespaces
```

### Step 11: Update Repository Configuration

```bash
# Update external-dns to use new API permanently
mv infrastructure/base/external-dns/release.yaml infrastructure/base/external-dns/release-old-api.yaml.bak
mv infrastructure/base/external-dns/release-new-api.yaml infrastructure/base/external-dns/release.yaml

mv infrastructure/base/external-dns/secret.yaml infrastructure/base/external-dns/secret-old-api.yaml.bak
mv infrastructure/base/external-dns/secret-new-api.yaml infrastructure/base/external-dns/secret.yaml

# Commit changes
git add infrastructure/base/external-dns/
git commit -m "Migrate external-dns to new Hetzner Cloud DNS API

- Update external-dns to use USE_CLOUD_API=true
- Replace DNS API token with Cloud API token
- Change txtOwnerId to avoid conflicts
- Backup old configuration files
"
git push
```

### Step 12: Cleanup Old Cluster

**Only after 48 hours of stable operation:**

```bash
# Export KUBECONFIG to old cluster
export KUBECONFIG=~/.kube/config-old

# Delete all applications (let Flux handle new cluster)
flux suspend kustomization apps
flux suspend kustomization infrastructure

# Or manually delete old Hetzner servers
# Via Hetzner Cloud Console or CLI

# Keep backups for 30 days before deleting
```

## Rollback Plan

### If Issues Occur During Migration

**Before DNS Migration (Step 9)**:
- Simply switch back to old cluster
- No changes to DNS needed
- Zero impact

**After DNS Migration (Step 9+)**:
1. **Cannot revert DNS to old API** - one-way migration
2. **Can point DNS back to old cluster IPs**:
   ```bash
   # In Hetzner Cloud Console DNS:
   # Update A records back to old control plane IP
   OLD_CTRL_IP="<old-cluster-ip>"

   # Update each record:
   # linkding.k8s-demo.de → OLD_CTRL_IP
   # wordpress.k8s-demo.de → OLD_CTRL_IP
   # etc.
   ```

3. **Wait for DNS propagation** (5-15 minutes with lowered TTL)

4. **Verify rollback**:
   ```bash
   dig linkding.k8s-demo.de +short
   # Should return OLD_CTRL_IP

   curl https://linkding.k8s-demo.de
   # Should work with old cluster
   ```

## Post-Migration

### 24 Hours After Migration

- [ ] Verify all applications accessible
- [ ] Check SSL certificates issued correctly
- [ ] Monitor error logs for issues
- [ ] Test all critical user journeys

### 48 Hours After Migration

- [ ] Increase DNS TTL back to normal (3600 or higher)
- [ ] Remove old cluster from Hetzner Console
- [ ] Update documentation with new IPs
- [ ] Clean up backup files (after verification)

### 30 Days After Migration

- [ ] Delete old cluster backups (if everything stable)
- [ ] Remove old external-dns configuration backups
- [ ] Archive migration notes

## Troubleshooting

### External-DNS Not Creating Records

```bash
# Check logs
kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns -f

# Common issues:
# 1. Wrong API token (Cloud vs DNS token)
# 2. USE_CLOUD_API not set to "true"
# 3. DNS zone not migrated to new API yet
# 4. Insufficient token permissions
```

### Applications Not Accessible After DNS Change

```bash
# Check DNS resolution
dig yourdomain.k8s-demo.de +short

# Check ingress
kubectl get ingress --all-namespaces

# Check ingress controller
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik -f

# Check certificates
kubectl get certificate --all-namespaces
kubectl describe certificate -n <namespace> <cert-name>
```

### SSL Certificates Not Issuing

```bash
# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager -f

# Check certificate requests
kubectl get certificaterequest --all-namespaces

# Check challenges
kubectl get challenges --all-namespaces

# Describe failing certificate
kubectl describe certificate -n <namespace> <cert-name>
```

## Summary

This migration strategy provides:

✅ **Zero-downtime option**: Deploy new cluster, test thoroughly, switch DNS
✅ **Rollback capability**: Can revert DNS to old cluster if needed
✅ **Data preservation**: Complete backup and restore procedures
✅ **Testing before go-live**: Verify everything works before DNS switch
✅ **Monitoring**: Clear verification steps at each stage

**Estimated Total Duration**: 3-4 hours (plus 24h for TTL lowering)

**Recommended Schedule**:
- **Day 0**: Lower DNS TTL, create backups
- **Day 1**: Deploy new cluster, install apps, test thoroughly
- **Day 1 (evening/weekend)**: Switch DNS during low-traffic period
- **Day 1-3**: Monitor closely
- **Day 3**: Clean up old cluster if stable
