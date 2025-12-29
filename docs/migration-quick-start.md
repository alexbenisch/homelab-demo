# Migration Quick Start

**TL;DR**: Move from manual cloud-init cluster to Terraform-managed cluster + migrate DNS from old API to new Hetzner Cloud DNS API.

## What You Need

1. **Hetzner Cloud API Token** - For Terraform to create servers
2. **Hetzner Cloud API Token** - For new DNS API (can be the same token)
3. **GitHub Secrets** - `HCLOUD_TOKEN` and `USER_PASSWORD`
4. **Backups** - All your PersistentVolume data
5. **Time** - ~4 hours total (1 hour prep + 3 hours migration)

## Critical Information

### ⚠️ DNS Migration is One-Way
**Once you migrate the DNS zone to the new API, you CANNOT go back to the old API.**

However, you CAN point DNS records back to your old cluster if needed.

### The New External-DNS Config

Your external-dns webhook already supports both APIs! Just add:
```yaml
- name: USE_CLOUD_API
  value: "true"
```

## 30-Second Overview

```
Day -1: Lower DNS TTL to 300s
Day 0:  Create backups
Day 1:  Deploy new cluster → Test apps → Switch DNS → Monitor
Day 2:  Verify stable → Clean up old cluster
```

## 3-Phase Migration

### Phase 1: Prep (No Risk)
```bash
# 1. Lower DNS TTL (24h before)
# 2. Backup everything
mkdir ~/homelab-migration-backup
kubectl get all --all-namespaces -o yaml > ~/homelab-migration-backup/all-resources.yaml
# ... backup PV data ...

# 3. Deploy new cluster
# GitHub Actions → Terraform Deployment → Run with "apply"

# 4. Configure workers
# Get k3s token from control plane, configure workers
```

### Phase 2: Migrate (Brief Downtime)
```bash
# 1. Install Flux on new cluster
# 2. Deploy apps via GitOps
# 3. Restore data from backups
# 4. Test via /etc/hosts (before DNS change)

# 5. Migrate DNS zone
# Hetzner Console → DNS → Import k8s-demo.de

# 6. Update DNS records
# Point all subdomains to new cluster IP

# 7. Wait for propagation (5-15 min)
```

### Phase 3: Cleanup (No Risk)
```bash
# Monitor for 48 hours
# If stable: destroy old cluster
# Increase DNS TTL back to 3600s
```

## Key Commands

### Create New Cluster
```bash
# Via GitHub Actions
Actions → Terraform Deployment → Run workflow → "apply"
```

### Get New Cluster IP
```bash
# From Terraform output or Hetzner Console
NEW_IP="x.x.x.x"
```

### Test Before DNS Switch
```bash
curl -H "Host: linkding.k8s-demo.de" http://$NEW_IP
```

### Migrate DNS
```bash
# 1. Hetzner Console → DNS → Import k8s-demo.de
# 2. Update A records:
#    linkding.k8s-demo.de → NEW_IP
#    wordpress.k8s-demo.de → NEW_IP
#    ... etc ...
```

### Verify DNS
```bash
dig linkding.k8s-demo.de +short  # Should show NEW_IP
curl https://linkding.k8s-demo.de  # Should work
```

## Emergency Rollback

```bash
# Update DNS records back to old cluster IP
# Via Hetzner Cloud Console → DNS → Edit records
# Wait 5-15 minutes for propagation
```

## Documents You Need

1. **[Full Strategy](migration-strategy.md)** - Complete step-by-step guide (read this!)
2. **[Checklist](migration-checklist.md)** - Track your progress
3. **[Rollback Guide](migration-rollback.md)** - If things go wrong

## Timeline

### 24 Hours Before
- [ ] Lower DNS TTL to 300s

### Day 0 (Prep)
- [ ] Create backups (1 hour)
- [ ] Deploy new cluster via GitHub Actions (5 minutes)
- [ ] Configure workers (10 minutes)
- [ ] Install Flux (10 minutes)
- [ ] Deploy apps (15 minutes)
- [ ] Restore data (30 minutes)
- [ ] Test thoroughly (30 minutes)

### Day 1 (Migration)
- [ ] Migrate DNS zone to new API (5 minutes)
- [ ] Update external-dns config (10 minutes)
- [ ] Update DNS records (10 minutes)
- [ ] Wait for propagation (15 minutes)
- [ ] Verify all apps work (30 minutes)
- [ ] Monitor (rest of day)

### Day 2-3
- [ ] Continue monitoring
- [ ] Fix any minor issues
- [ ] Verify stability

### Day 3+
- [ ] Increase DNS TTL back to 3600s
- [ ] Destroy old cluster
- [ ] Archive migration docs

## Common Issues

### "External-DNS not creating records"
- Check `USE_CLOUD_API: "true"` is set
- Verify Cloud API token (not DNS API token)
- Check zone was migrated to new API

### "SSL certificates not issuing"
- Check cert-manager logs
- Verify DNS records point to correct IP
- Check Let's Encrypt rate limits

### "Can't access applications after DNS switch"
- Check DNS resolution: `dig yourapp.k8s-demo.de`
- Check ingress: `kubectl get ingress -A`
- Check traefik logs

## Success Criteria

✅ All nodes in new cluster are Ready
✅ All pods are Running
✅ All PVCs are Bound
✅ All apps accessible via `/etc/hosts` test
✅ DNS points to new cluster
✅ All apps accessible via HTTPS
✅ SSL certificates issued
✅ No errors in logs
✅ Stable for 48 hours

## Still Confused?

Read the [Full Migration Strategy](migration-strategy.md) - it has everything you need!

## Questions to Ask Yourself

Before starting:
- [ ] Do I have backups of all data?
- [ ] Have I tested the Terraform deployment?
- [ ] Do I have both old and new API tokens?
- [ ] Is my maintenance window scheduled?
- [ ] Have I lowered DNS TTL?

Before switching DNS:
- [ ] Is the new cluster fully deployed?
- [ ] Are all apps working via IP test?
- [ ] Is data restored correctly?
- [ ] Do I know how to rollback?

After DNS switch:
- [ ] Is DNS resolving to new IPs?
- [ ] Are all apps accessible?
- [ ] Are SSL certs working?
- [ ] Are logs clean?

## Remember

- **DNS migration is one-way** (zone, not records)
- **Test everything before switching DNS**
- **Lower TTL makes rollback faster**
- **Keep old cluster running for 48 hours**
- **Communicate with users**
- **Don't panic - rollback is easy**

## Next Steps

1. Read the [Full Migration Strategy](migration-strategy.md)
2. Print the [Migration Checklist](migration-checklist.md)
3. Create your backups
4. Deploy new cluster
5. Test thoroughly
6. Switch DNS during low-traffic period
7. Monitor and celebrate! 🎉
