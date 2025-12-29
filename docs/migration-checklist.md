# Migration Checklist

Use this checklist to track your progress through the cluster and DNS API migration.

## Pre-Migration (Day 0)

### Backups
- [ ] Export all PersistentVolume data
  - [ ] Linkding data backed up
  - [ ] Wallabag data backed up
  - [ ] WordPress files backed up
  - [ ] WordPress MySQL backed up
  - [ ] Grafana data backed up
  - [ ] Tested-Django PostgreSQL backed up
- [ ] Save current kubeconfig
- [ ] Export all Kubernetes secrets
- [ ] Export all Kubernetes resources (deployments, services, ingress, etc.)
- [ ] Document all DNS records
- [ ] Backup SOPS age key

### Hetzner Setup
- [ ] Hetzner Cloud API token created (for Terraform)
- [ ] Hetzner Cloud API token created (for new DNS API)
- [ ] Verify you can access Hetzner Cloud Console
- [ ] Review DNS records at https://dns.hetzner.com

### GitHub Setup
- [ ] GitHub secrets configured
  - [ ] `HCLOUD_TOKEN` added
  - [ ] `USER_PASSWORD` added
- [ ] Test Terraform workflow with `plan` action
- [ ] Verify workflow runs successfully

### Communication
- [ ] Users notified of maintenance window
- [ ] Migration scheduled during low-traffic period

### DNS TTL
- [ ] **Lower TTL to 300 seconds on all DNS records** (do 24h before migration)
  - [ ] k8s-demo.de
  - [ ] linkding.k8s-demo.de
  - [ ] wordpress.k8s-demo.de
  - [ ] demo-django.k8s-demo.de
  - [ ] demo-api.k8s-demo.de
  - [ ] grafana.k8s-demo.de
  - [ ] tested-django.k8s-demo.de

## Migration Day (Day 1)

### Phase 1: Deploy New Cluster

- [ ] Deploy new cluster via Terraform
  - [ ] GitHub Actions workflow completed successfully
  - [ ] Control plane node running
  - [ ] Worker 1 node running
  - [ ] Worker 2 node running
- [ ] Wait for cloud-init (2-3 minutes)
- [ ] Configure workers with k3s token
  - [ ] Worker 1 joined cluster
  - [ ] Worker 2 joined cluster
- [ ] Verify all nodes Ready: `kubectl get nodes`
- [ ] Get kubeconfig from new cluster
- [ ] Save new cluster IPs

### Phase 2: Install Infrastructure

- [ ] Create SOPS age secret in flux-system namespace
- [ ] Install Flux on new cluster
- [ ] Create Git source
- [ ] Create infrastructure kustomization
- [ ] Wait for infrastructure deployment
  - [ ] external-dns deployed
  - [ ] cert-manager deployed (if applicable)
  - [ ] ingress controller deployed

### Phase 3: Deploy Applications

- [ ] Create apps kustomization
- [ ] Wait for all apps to deploy
  - [ ] Linkding pod running
  - [ ] Wallabag pod running
  - [ ] WordPress pods running
  - [ ] MySQL pod running
  - [ ] Demo Django pod running
  - [ ] Demo API pod running
  - [ ] Grafana pod running
  - [ ] Tested Django pod running
  - [ ] PostgreSQL pod running
- [ ] All PVCs bound

### Phase 4: Restore Data

- [ ] Restore Linkding data
- [ ] Restore Wallabag data
- [ ] Restore WordPress files
- [ ] Restore WordPress database
- [ ] Restore Grafana data
- [ ] Restore Tested-Django database
- [ ] Restart all pods
- [ ] Verify data restored correctly

### Phase 5: Test New Cluster (Without DNS)

- [ ] Test via /etc/hosts or Host header
  - [ ] Linkding accessible and data present
  - [ ] Wallabag accessible and data present
  - [ ] WordPress accessible and data present
  - [ ] Demo Django accessible
  - [ ] Demo API health check passes
  - [ ] Grafana accessible and dashboards present
  - [ ] Tested Django accessible
- [ ] All ingress rules working
- [ ] All services responding correctly

### Phase 6: Prepare DNS Migration

- [ ] Create new Cloud API token in Hetzner Console
- [ ] Update external-dns secret template with new token
- [ ] Encrypt secret with SOPS
- [ ] Copy release-new-api.yaml to release.yaml (don't commit yet)
- [ ] Copy secret-new-api.yaml to secret.yaml (don't commit yet)

### Phase 7: DNS Migration (POINT OF NO RETURN)

- [ ] **Migrate DNS zone to new Hetzner Cloud DNS**
  - [ ] Log into https://console.hetzner.cloud
  - [ ] Go to DNS section
  - [ ] Import/add zone k8s-demo.de
  - [ ] Verify all existing records present

- [ ] **Update DNS records to point to new cluster**

  **Option A: Manual (faster)**
  - [ ] Update linkding.k8s-demo.de → NEW_CTRL_IP
  - [ ] Update wordpress.k8s-demo.de → NEW_CTRL_IP
  - [ ] Update demo-django.k8s-demo.de → NEW_CTRL_IP
  - [ ] Update demo-api.k8s-demo.de → NEW_CTRL_IP
  - [ ] Update grafana.k8s-demo.de → NEW_CTRL_IP
  - [ ] Update tested-django.k8s-demo.de → NEW_CTRL_IP

  **Option B: Automated (slower)**
  - [ ] Commit new external-dns configuration
  - [ ] Push to repository
  - [ ] Wait for Flux reconciliation
  - [ ] Wait for external-dns to create records

### Phase 8: Verify DNS Propagation

- [ ] Wait 5-15 minutes for DNS propagation
- [ ] Test DNS resolution
  - [ ] `dig linkding.k8s-demo.de` → NEW_CTRL_IP
  - [ ] `dig wordpress.k8s-demo.de` → NEW_CTRL_IP
  - [ ] `dig demo-django.k8s-demo.de` → NEW_CTRL_IP
  - [ ] `dig demo-api.k8s-demo.de` → NEW_CTRL_IP
  - [ ] `dig grafana.k8s-demo.de` → NEW_CTRL_IP
  - [ ] `dig tested-django.k8s-demo.de` → NEW_CTRL_IP
- [ ] Test HTTPS access
  - [ ] `curl https://linkding.k8s-demo.de`
  - [ ] `curl https://wordpress.k8s-demo.de`
  - [ ] `curl https://demo-django.k8s-demo.de`
  - [ ] `curl https://demo-api.k8s-demo.de/health`
  - [ ] `curl https://grafana.k8s-demo.de`
  - [ ] `curl https://tested-django.k8s-demo.de`

### Phase 9: Monitor

- [ ] Monitor pod status
- [ ] Monitor external-dns logs
- [ ] Monitor ingress controller logs
- [ ] Check certificate issuance
- [ ] Test all user journeys
- [ ] No errors in logs

## Post-Migration

### 24 Hours After

- [ ] All applications stable
- [ ] SSL certificates issued correctly
- [ ] No error spikes in logs
- [ ] User feedback positive
- [ ] Update kubeconfig permanently

### 48 Hours After

- [ ] Increase DNS TTL back to 3600
- [ ] Document new cluster IPs
- [ ] Update runbooks/documentation
- [ ] Decommission old cluster
  - [ ] Delete old Hetzner servers
  - [ ] Remove old firewall rules
  - [ ] Remove old network

### 7 Days After

- [ ] Remove /etc/hosts entries (if used)
- [ ] Clean up old kubeconfig
- [ ] Archive migration logs

### 30 Days After

- [ ] Delete old cluster backups (if stable)
- [ ] Remove old external-dns configuration backups
- [ ] Archive migration documentation

## Rollback Checklist

If you need to rollback:

- [ ] **CANNOT revert DNS zone to old API** (one-way migration)
- [ ] Update DNS records in Hetzner Cloud Console back to old cluster IP
- [ ] Wait for DNS propagation
- [ ] Verify old cluster accessible
- [ ] Monitor old cluster
- [ ] Restore data from backups if needed

## Notes and Issues

Use this space to document any issues encountered:

```
Issue 1:
Solution:

Issue 2:
Solution:

Issue 3:
Solution:
```

## Key Information

**Old Cluster IPs:**
- Control Plane: `___________________`
- Worker 1: `___________________`
- Worker 2: `___________________`

**New Cluster IPs:**
- Control Plane: `___________________`
- Worker 1: `___________________`
- Worker 2: `___________________`

**API Tokens:**
- Old DNS API Token: `stored in SOPS`
- New Cloud API Token: `stored in SOPS`
- Hetzner Cloud Token (Terraform): `GitHub secret HCLOUD_TOKEN`

**Critical Contacts:**
- DNS Admin: `___________________`
- Infrastructure Owner: `___________________`
- On-call: `___________________`

**Timing:**
- TTL Lowered: `___________________`
- Migration Start: `___________________`
- DNS Switched: `___________________`
- Migration Complete: `___________________`
