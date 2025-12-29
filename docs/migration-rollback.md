# Migration Rollback Guide

Quick reference for rolling back the cluster migration if issues occur.

## ⚠️ Important Constraints

### DNS Zone Migration is One-Way
**You CANNOT revert the DNS zone back to the old API** after migrating to the new Hetzner Cloud DNS API.

However, you CAN:
- Point DNS records back to the old cluster IP addresses
- Continue using the old cluster with the new DNS API
- Manage DNS via the new Hetzner Cloud Console

## Rollback Scenarios

### Scenario 1: Before DNS Migration (Low Risk)

**When**: Issues found during new cluster testing (Steps 1-8)

**Action**: Simply continue using old cluster
- No DNS changes made yet
- No user impact
- New cluster can be destroyed and recreated

**Steps**:
```bash
# Continue using old cluster
export KUBECONFIG=~/.kube/config-old
kubectl get nodes

# Destroy new cluster if needed
cd terraform
terraform destroy -auto-approve

# No further action required
```

### Scenario 2: After DNS Zone Migration (Medium Risk)

**When**: Zone migrated to new API but records not yet updated (Step 9 partial)

**Action**: Update DNS records in new console to point to old cluster

**Steps**:
1. Log into https://console.hetzner.cloud
2. Go to **DNS** → **k8s-demo.de**
3. Update all A records to old cluster IP:
   - linkding.k8s-demo.de → `OLD_CTRL_IP`
   - wordpress.k8s-demo.de → `OLD_CTRL_IP`
   - demo-django.k8s-demo.de → `OLD_CTRL_IP`
   - demo-api.k8s-demo.de → `OLD_CTRL_IP`
   - grafana.k8s-demo.de → `OLD_CTRL_IP`
   - tested-django.k8s-demo.de → `OLD_CTRL_IP`

4. Wait for DNS propagation (5-15 minutes with lowered TTL)

5. Verify:
   ```bash
   dig linkding.k8s-demo.de +short
   # Should return OLD_CTRL_IP

   curl https://linkding.k8s-demo.de
   # Should work
   ```

### Scenario 3: After DNS Records Updated (High Risk)

**When**: DNS pointing to new cluster but issues discovered (Step 9 complete)

**Critical**: Users are now hitting the new cluster

**Option A: Quick Rollback** (5-15 minutes downtime)

1. **Immediate**: Update DNS records back to old cluster (see Scenario 2)

2. **Switch to old cluster**:
   ```bash
   export KUBECONFIG=~/.kube/config-old
   kubectl get nodes
   ```

3. **Verify old cluster healthy**:
   ```bash
   kubectl get pods --all-namespaces
   kubectl get ingress --all-namespaces
   ```

4. **Wait for DNS propagation**: 5-15 minutes

5. **Verify services**:
   ```bash
   curl https://linkding.k8s-demo.de
   curl https://wordpress.k8s-demo.de
   # etc.
   ```

**Option B: Fix Forward** (recommended if issue is minor)

If the issue is minor, consider fixing it rather than rolling back:

1. **Identify the issue**:
   ```bash
   kubectl logs -n <namespace> <pod-name>
   kubectl describe pod -n <namespace> <pod-name>
   ```

2. **Common fixes**:
   - Restart problematic pod
   - Fix configuration
   - Restore missing data
   - Update ingress/service

3. **Test fix**:
   ```bash
   curl https://affected-app.k8s-demo.de
   ```

## Emergency Rollback Commands

### Get Old Cluster IP
```bash
# From backup notes or Hetzner Console
OLD_CTRL_IP="<old-cluster-control-plane-ip>"
```

### Update DNS Records (Hetzner Cloud Console)
```
1. Go to: https://console.hetzner.cloud
2. DNS → k8s-demo.de
3. Edit each A record:
   - linkding.k8s-demo.de → OLD_CTRL_IP
   - wordpress.k8s-demo.de → OLD_CTRL_IP
   - demo-django.k8s-demo.de → OLD_CTRL_IP
   - demo-api.k8s-demo.de → OLD_CTRL_IP
   - grafana.k8s-demo.de → OLD_CTRL_IP
   - tested-django.k8s-demo.de → OLD_CTRL_IP
```

### Update DNS Records (via API - Faster)
```bash
# Install hcloud CLI
# Get your Cloud API token

export HCLOUD_TOKEN="your-cloud-api-token"
OLD_CTRL_IP="<old-cluster-ip>"

# Get zone ID
ZONE_ID=$(curl -H "Auth-API-Token: $HCLOUD_TOKEN" https://dns.hetzner.com/api/v1/zones | jq -r '.zones[] | select(.name=="k8s-demo.de") | .id')

# Update each record (replace RECORD_ID with actual IDs)
# You'll need to get record IDs first
curl -X GET \
  -H "Auth-API-Token: $HCLOUD_TOKEN" \
  https://dns.hetzner.com/api/v1/records?zone_id=$ZONE_ID

# Then update each:
curl -X PUT \
  -H "Auth-API-Token: $HCLOUD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"value\":\"$OLD_CTRL_IP\",\"ttl\":300,\"type\":\"A\",\"name\":\"linkding\",\"zone_id\":\"$ZONE_ID\"}" \
  https://dns.hetzner.com/api/v1/records/RECORD_ID
```

### Verify DNS Propagation
```bash
# Check DNS
watch -n 5 'dig linkding.k8s-demo.de +short'

# Should eventually show OLD_CTRL_IP
```

### Test Services
```bash
# Test each service
for subdomain in linkding wordpress demo-django demo-api grafana tested-django; do
  echo "Testing $subdomain.k8s-demo.de..."
  curl -I "https://$subdomain.k8s-demo.de" 2>&1 | head -n 1
done
```

## Post-Rollback Actions

### Immediate (First Hour)
- [ ] Monitor old cluster logs
- [ ] Verify all services accessible
- [ ] Check for error spikes
- [ ] Notify users of resolution

### Short Term (24 Hours)
- [ ] Investigate root cause of rollback
- [ ] Document lessons learned
- [ ] Update migration plan
- [ ] Decide on retry timeline

### Long Term (1 Week)
- [ ] Fix issues that caused rollback
- [ ] Test fixes on new cluster
- [ ] Plan second migration attempt
- [ ] Keep old cluster running until successful migration

## Data Recovery After Rollback

If you need to recover data from new cluster after rollback:

```bash
# Switch to new cluster
export KUBECONFIG=~/.kube/config-new

# Export any new data created during migration
kubectl exec -n <namespace> <pod> -- tar czf - /data > data-from-new-cluster.tar.gz

# Switch back to old cluster
export KUBECONFIG=~/.kube/config-old

# Restore to old cluster if needed
kubectl cp data-from-new-cluster.tar.gz <namespace>/<pod>:/tmp/
kubectl exec -n <namespace> <pod> -- tar xzf /tmp/data-from-new-cluster.tar.gz -C /
```

## Communication Templates

### User Notification - Rollback in Progress
```
Subject: [Maintenance] Cluster Migration Rollback in Progress

We are rolling back the cluster migration due to technical issues.

Expected impact: 5-15 minutes of intermittent access
Current status: Updating DNS records back to original cluster
ETA: DNS propagation complete in ~15 minutes

We will notify when services are fully restored.
```

### User Notification - Rollback Complete
```
Subject: [Resolved] Cluster Migration Rollback Complete

The cluster migration rollback has been completed successfully.

All services are now running on the original cluster.
DNS records have been restored to point to the original infrastructure.

We apologize for any inconvenience. We will investigate the issues and
communicate a new migration timeline.
```

## Decision Matrix

### Should You Rollback?

**Rollback if**:
- Critical services completely down
- Data loss detected
- Security issue discovered
- Multiple applications failing
- Unable to fix within 30 minutes

**Don't Rollback if**:
- Single non-critical app failing
- Minor performance issue
- Issue can be fixed quickly (< 15 min)
- Only cosmetic problems
- Users not significantly impacted

**Fix Forward if**:
- Issue is well understood
- Fix is simple and tested
- Rollback would cause more disruption
- Data already migrated to new cluster
- Users already adapted to new cluster

## Key Contacts During Rollback

- **DNS Admin**: ___________________
- **Infrastructure Lead**: ___________________
- **Application Owners**: ___________________
- **On-Call Engineer**: ___________________
- **Hetzner Support**: support@hetzner.com

## Rollback Testing

Before migration, test the rollback procedure:

```bash
# 1. Lower TTL on test record
# 2. Create test record pointing to new cluster
# 3. Verify propagation
# 4. Update test record back to old cluster
# 5. Verify propagation
# 6. Measure time taken

# This validates:
# - DNS update process
# - Propagation time with lowered TTL
# - Your ability to quickly switch DNS
```

## Lessons Learned Template

After rollback, document:

**What went wrong?**
-

**Why did it go wrong?**
-

**What could have prevented it?**
-

**What will we do differently next time?**
-

**Timeline of events:**
-

**Impact assessment:**
-

## Remember

1. **Stay calm**: Rollback is a planned contingency
2. **Communicate**: Keep users informed
3. **Document**: Record what happened and why
4. **Learn**: Use this to improve the next attempt
5. **DNS is one-way**: You cannot revert to old DNS API, only change record values
6. **Keep backups**: Don't delete old cluster until 100% confident
7. **Lower TTL helps**: 300s TTL means 5-15min rollback time vs hours with 3600s TTL
