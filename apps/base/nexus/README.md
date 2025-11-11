# Nexus Repository Manager

Nexus 3 is a universal artifact repository manager that supports Docker images, Maven, npm, PyPI, and many other formats.

## Access

- **UI**: `https://nexus.k8s-demo.de`
- **Docker Registry**: Access via repository path (see Docker Registry setup below)

## Initial Setup

### 1. Admin Password

The admin password is stored in a SOPS-encrypted secret (`secret.yaml`). The password is: `gaic4aeShae8hahSh2ay1iRui`

**Important**: On first startup, Nexus generates a random password. You'll need to change it to match the secret:

```bash
# Wait for Nexus to fully start (takes 2-3 minutes)
kubectl wait --for=condition=ready pod -l app=nexus -n nexus --timeout=5m

# Get the initial random password
kubectl exec -n nexus deployment/nexus -- cat /nexus-data/admin.password

# Use this password to login, then change it in the setup wizard
```

### 2. Complete Setup Wizard

1. Visit `https://nexus.k8s-demo.de`
2. Click "Sign In" (top right)
3. Username: `admin`
4. Password: (use the random password from step 1)
5. Follow the setup wizard:
   - **Change admin password to**: `gaic4aeShae8hahSh2ay1iRui` (matches the secret)
   - Configure anonymous access:
     - ✅ Enable for easier k8s image pulls (recommended for homelab)
     - ❌ Disable for better security
   - Click "Finish"

### 3. Enable Docker Bearer Token Realm

**This step is required before creating Docker repositories:**

1. Go to **Settings (gear icon)** → **Security** → **Realms**
2. Add **Docker Bearer Token Realm** to the **Active** list (drag from Available to Active)
3. Click **Save**

This realm is required for:
- Docker client authentication
- Anonymous pulls from Docker repositories
- Proper token-based authentication

### 4. Configure Docker Registry

#### Create Docker Hosted Repository

1. Go to **Settings (gear icon)** → **Repositories** → **Create repository**
2. Select **docker (hosted)**
3. Configure:
   - **Name**: `docker-hosted`
   - **HTTP**: Leave blank (will use connector on port 5000, but access via path)
   - **Allow anonymous docker pull**: ✓ (for easier k8s usage) or ✗ (for security)
   - **Enable Docker V1 API**: ✗ (not needed)
4. Click **Create repository**

**Note**: Without a dedicated subdomain or port forwarding, Docker images are accessed via the repository path: `nexus.k8s-demo.de/repository/docker-hosted/`

#### Create Docker Group Repository (Optional)

This allows you to proxy Docker Hub and host images together:

1. **Create repository** → **docker (proxy)**
   - **Name**: `docker-proxy`
   - **Remote storage**: `https://registry-1.docker.io`
   - **Docker Index**: Use Docker Hub
   - Click **Create repository**

2. **Create repository** → **docker (group)**
   - **Name**: `docker-group`
   - **HTTP**: Leave blank (use 5000 from hosted)
   - **Member repositories**: Add both `docker-hosted` and `docker-proxy`
   - Click **Create repository**

## Using the Docker Registry

### Configure Docker Client

The Docker registry is accessed via the repository path:

```bash
# Login to the registry (using the repository path)
docker login nexus.k8s-demo.de
# When prompted for repository, you can specify: nexus.k8s-demo.de/repository/docker-hosted
# Username: admin (or create a new user in Nexus)
# Password: gaic4aeShae8hahSh2ay1iRui
```

**Note**: Nexus serves Docker registries on repository paths like `/repository/docker-hosted/` rather than dedicated ports when using a single ingress. This is the standard approach for Nexus behind a reverse proxy.

### Push Images

```bash
# Tag your image with the full repository path
docker tag cluster-dashboard:latest nexus.k8s-demo.de/repository/docker-hosted/cluster-dashboard:latest

# Push to registry
docker push nexus.k8s-demo.de/repository/docker-hosted/cluster-dashboard:latest

# Pull from registry
docker pull nexus.k8s-demo.de/repository/docker-hosted/cluster-dashboard:latest

# List images in registry via Nexus REST API
curl -u admin:gaic4aeShae8hahSh2ay1iRui \
  "https://nexus.k8s-demo.de/service/rest/v1/components?repository=docker-hosted"
```

### Pull Images from Kubernetes

#### Option 1: Anonymous Pull (if enabled)

If you enabled anonymous pulls when creating the repository, no configuration needed:

```yaml
spec:
  containers:
    - name: cluster-dashboard
      image: nexus.k8s-demo.de/repository/docker-hosted/cluster-dashboard:latest
```

#### Option 2: With Authentication

Create a Docker registry secret:

```bash
kubectl create secret docker-registry nexus-registry \
  --docker-server=nexus.k8s-demo.de \
  --docker-username=admin \
  --docker-password=gaic4aeShae8hahSh2ay1iRui \
  -n cluster-dashboard

# Use in deployment by patching the service account
kubectl patch serviceaccount cluster-dashboard -n cluster-dashboard \
  -p '{"imagePullSecrets": [{"name": "nexus-registry"}]}'
```

Or add to deployment manifest:

```yaml
spec:
  imagePullSecrets:
    - name: nexus-registry
  containers:
    - name: cluster-dashboard
      image: nexus.k8s-demo.de/repository/docker-hosted/cluster-dashboard:latest
```

## Configuration

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `INSTALL4J_ADD_VM_PARAMS` | `-Xms1024m -Xmx1024m` | JVM memory settings |

### Storage

- **PVC**: 50Gi
- **Mount**: `/nexus-data`
- **Storage Class**: `local-path`

### Ports

| Port | Service | Description |
|------|---------|-------------|
| 8081 | Nexus UI | Web interface |
| 5000 | Docker Registry | Docker API |

### Ingress

- **nexus.k8s-demo.de**: Nexus web UI (port 8081) and Docker registry (port 5000)

Uses Let's Encrypt for TLS certificates.

## Deployment

This deployment uses Flux CD for GitOps:

```bash
# Commit the changes
git add apps/base/nexus apps/staging/nexus apps/staging/kustomization.yaml
git commit -m "Add Nexus Repository Manager"
git push

# Trigger Flux reconciliation
flux reconcile kustomization apps --with-source

# Check status
kubectl get pods -n nexus
kubectl get ingress -n nexus

# View logs
kubectl logs -n nexus deployment/nexus -f
```

## Backup

### Backup Nexus Data

```bash
# Create backup
kubectl exec -n nexus deployment/nexus -- tar czf - /nexus-data > nexus-backup-$(date +%Y%m%d).tar.gz
```

### Restore from Backup

```bash
# Stop Nexus
kubectl scale deployment nexus -n nexus --replicas=0

# Restore data
cat nexus-backup-YYYYMMDD.tar.gz | kubectl exec -i -n nexus deployment/nexus -- tar xzf - -C /

# Start Nexus
kubectl scale deployment nexus -n nexus --replicas=1
```

## Troubleshooting

### Pod Not Starting

```bash
# Check events
kubectl describe pod -n nexus -l app=nexus

# Check logs
kubectl logs -n nexus -l app=nexus --tail=100

# Common issues:
# - Insufficient memory (needs at least 2Gi)
# - PVC not bound
# - Slow startup (can take 2-3 minutes)
```

### Cannot Access UI

```bash
# Check ingress
kubectl get ingress -n nexus

# Check service
kubectl get svc -n nexus

# Test from within cluster
kubectl run -n nexus test-nexus --rm -it --image=curlimages/curl --restart=Never -- curl -I http://nexus:8081
```

### Docker Push/Pull Fails

1. **Verify Docker Bearer Token Realm is enabled**:
   - Settings → Security → Realms
   - Ensure "Docker Bearer Token Realm" is in the Active list

2. **Check Nexus logs** for authentication errors:
   ```bash
   kubectl logs -n nexus deployment/nexus | grep -i docker
   ```

3. **Verify Docker registry** is configured in Nexus (port 5000):
   - Settings → Repositories → docker-hosted
   - Check HTTP port is set to 5000

4. **Test registry API**:
   ```bash
   # Test repository endpoint
   curl -u admin:gaic4aeShae8hahSh2ay1iRui \
     "https://nexus.k8s-demo.de/service/rest/v1/repositories"

   # List images in docker-hosted repository
   curl -u admin:gaic4aeShae8hahSh2ay1iRui \
     "https://nexus.k8s-demo.de/service/rest/v1/components?repository=docker-hosted"
   ```

5. **Check Docker client configuration**:
   ```bash
   # Verify login
   docker login nexus.k8s-demo.de

   # Check stored credentials
   cat ~/.docker/config.json | grep nexus
   ```

### Performance Issues

Increase memory limits in `deployment.yaml`:

```yaml
env:
  - name: INSTALL4J_ADD_VM_PARAMS
    value: "-Xms2048m -Xmx2048m -XX:MaxDirectMemorySize=2048m"

resources:
  requests:
    memory: 4Gi
  limits:
    memory: 6Gi
```

## Security Best Practices

1. **Change default password** immediately after first login
2. **Disable anonymous access** unless specifically needed
3. **Create dedicated users** for CI/CD pipelines (don't use admin)
4. **Enable Docker Bearer Token** authentication
5. **Set up LDAP/SSO** for user management
6. **Regular backups** of `/nexus-data`
7. **Monitor disk usage** (50Gi can fill up quickly with images)

## Additional Resources

- [Nexus Documentation](https://help.sonatype.com/repomanager3)
- [Docker Registry Configuration](https://help.sonatype.com/repomanager3/nexus-repository-administration/formats/docker-registry)
- [Nexus Repository Docker Hub](https://hub.docker.com/r/sonatype/nexus3/)
