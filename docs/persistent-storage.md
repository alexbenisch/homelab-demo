# Persistent Storage in Kubernetes

Guide for adding persistent storage to applications using PersistentVolumeClaims (PVCs).

## Overview

Persistent storage ensures that data survives pod restarts, updates, and failures. In Kubernetes, this is achieved using PersistentVolumeClaims (PVCs) that request storage from the cluster.

## Adding Persistent Storage to an Application

### 1. Create a PersistentVolumeClaim

Create a `storage.yaml` file in your application's base directory:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: <app-name>-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

**Access Modes:**
- `ReadWriteOnce` (RWO) - Volume can be mounted as read-write by a single node
- `ReadOnlyMany` (ROX) - Volume can be mounted as read-only by many nodes
- `ReadWriteMany` (RWX) - Volume can be mounted as read-write by many nodes

### 2. Update the Deployment

Add volume mounts and volumes to your deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app-name>
spec:
  template:
    spec:
      containers:
        - name: <app-name>
          volumeMounts:
            - name: <volume-name>
              mountPath: /path/to/data
      volumes:
        - name: <volume-name>
          persistentVolumeClaim:
            claimName: <app-name>-data-pvc
```

### 3. Add Security Context (Recommended)

Set proper permissions for the volume:

```yaml
spec:
  template:
    spec:
      securityContext:
        fsGroup: <gid>
        runAsUser: <uid>
        runAsGroup: <gid>
      containers:
        - name: <app-name>
          securityContext:
            allowPrivilegeEscalation: false
```

### 4. Update Kustomization

Add the storage.yaml to your kustomization resources:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - storage.yaml
```

## Example: Linkding with Persistent Storage

### Directory Structure
```
apps/base/linkding/
├── deployment.yaml
├── service.yaml
├── storage.yaml
├── kustomization.yaml
└── ...
```

### storage.yaml
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: linkding-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### deployment.yaml (relevant sections)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: linkding
spec:
  template:
    spec:
      securityContext:
        fsGroup: 33 # www-data group ID
        runAsUser: 33 # www-data user ID
        runAsGroup: 33 # www-data group ID

      containers:
        - name: linkding
          image: sissbruecker/linkding:1.31.0

          securityContext:
            allowPrivilegeEscalation: false

          volumeMounts:
            - name: linkding-data
              mountPath: /etc/linkding/data

      volumes:
        - name: linkding-data
          persistentVolumeClaim:
            claimName: linkding-data-pvc
```

## Applying Changes with GitOps

After committing and pushing your changes:

### 1. Push Changes to Git
```bash
git add .
git commit -m "Add persistent storage for <app-name>"
git push
```

### 2. Force Flux Reconciliation

**Reconcile entire kustomization:**
```bash
flux reconcile kustomization apps --with-source
```

**Reconcile specific kustomization:**
```bash
flux reconcile kustomization <kustomization-name> --with-source
```

**Reconcile git source then kustomization:**
```bash
flux reconcile source git <source-name>
flux reconcile kustomization <kustomization-name>
```

### 3. Verify Deployment

**Check Flux status:**
```bash
flux get kustomizations
```

**Check PVC status:**
```bash
kubectl get pvc -n <namespace>
```

Expected output:
```
NAME                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES
linkding-data-pvc     Bound    pvc-abc123...                             1Gi        RWO
```

**Check pod status:**
```bash
kubectl get pods -n <namespace>
kubectl describe pod -n <namespace> <pod-name>
```

**Verify volume mount:**
```bash
kubectl exec -n <namespace> <pod-name> -- df -h /path/to/data
```

## Troubleshooting

### PVC Stuck in Pending

**Check PVC events:**
```bash
kubectl describe pvc -n <namespace> <pvc-name>
```

**Common causes:**
- No storage class available
- No available storage matching the request
- Insufficient resources

**Check available storage classes:**
```bash
kubectl get storageclass
```

### Permission Denied Errors

**Check if fsGroup matches application user:**
```bash
kubectl exec -n <namespace> <pod-name> -- id
kubectl exec -n <namespace> <pod-name> -- ls -la /path/to/data
```

**Fix by updating securityContext in deployment with correct UID/GID**

### Pod Fails to Start After Adding Volume

**Check pod logs:**
```bash
kubectl logs -n <namespace> <pod-name>
```

**Check pod events:**
```bash
kubectl describe pod -n <namespace> <pod-name>
```

**Common issues:**
- Wrong mount path
- Application expects different permissions
- Volume already mounted by another pod (for ReadWriteOnce)

## Managing Storage

### Resize PVC

Edit the PVC (requires storage class to support expansion):
```bash
kubectl edit pvc -n <namespace> <pvc-name>
```

Update the storage request:
```yaml
spec:
  resources:
    requests:
      storage: 5Gi
```

### Backup Data

**Create a backup pod:**
```bash
kubectl run backup --image=busybox --rm -it --restart=Never \
  --overrides='
  {
    "spec": {
      "containers": [{
        "name": "backup",
        "image": "busybox",
        "stdin": true,
        "tty": true,
        "volumeMounts": [{
          "name": "data",
          "mountPath": "/data"
        }]
      }],
      "volumes": [{
        "name": "data",
        "persistentVolumeClaim": {
          "claimName": "<pvc-name>"
        }
      }]
    }
  }' -n <namespace> -- tar czf - /data > backup.tar.gz
```

### Delete PVC

**Warning: This will delete all data!**

```bash
# Remove from kustomization first
# Commit and push changes
# Reconcile Flux
flux reconcile kustomization <kustomization-name> --with-source

# Manually delete if needed
kubectl delete pvc -n <namespace> <pvc-name>
```

## Best Practices

1. **Always set storage requests appropriately** - Consider application data growth
2. **Use security contexts** - Ensure proper file permissions
3. **Test locally first** - Use port-forward to verify data persistence
4. **Monitor storage usage** - Set up alerts for PVC capacity
5. **Regular backups** - Don't rely solely on PVCs for data safety
6. **Use appropriate access modes** - RWO for single instance, RWX for multi-replica
7. **Document mount paths** - Keep track of where each app stores data

## Storage Requirements by Application Type

| Application Type | Typical Storage | Access Mode | Notes |
|-----------------|-----------------|-------------|-------|
| Database (PostgreSQL, MySQL) | 5-20Gi | RWO | Size based on data volume |
| File storage (Nextcloud) | 10-100Gi+ | RWO/RWX | Depends on users |
| Bookmark manager (Linkding) | 1-5Gi | RWO | Mostly database |
| Wiki (BookStack) | 2-10Gi | RWO | Documents + uploads |
| Media server (Jellyfin) | 100Gi+ | RWO/RWX | Large media files |
| Cache (Redis) | 1-5Gi | RWO | Memory snapshots |
