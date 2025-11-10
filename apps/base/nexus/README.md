# Nexus Repository Manager

Nexus 3 is a universal artifact repository manager that supports Docker images, Maven, npm, PyPI, and many other formats.

## Access

- **UI**: `https://nexus.k8s-demo.de`
- **Docker Registry**: `https://registry.k8s-demo.de`

## Initial Setup

### 1. Get Admin Password

Nexus generates a random admin password on first startup:

```bash
# Wait for Nexus to fully start (takes 2-3 minutes)
kubectl wait --for=condition=ready pod -l app=nexus -n nexus --timeout=5m

# Get the initial admin password
kubectl exec -n nexus deployment/nexus -- cat /nexus-data/admin.password
```

### 2. Complete Setup Wizard

1. Visit `https://nexus.k8s-demo.de`
2. Click "Sign In" (top right)
3. Username: `admin`
4. Password: (use the password from step 1)
5. Follow the setup wizard:
   - Change admin password (save it securely!)
   - Configure anonymous access (recommend: disable)
   - Click "Finish"

### 3. Configure Docker Registry

#### Create Docker Hosted Repository

1. Go to **Settings (gear icon)** → **Repositories** → **Create repository**
2. Select **docker (hosted)**
3. Configure:
   - **Name**: `docker-hosted`
   - **HTTP**: `5000` (already configured in deployment)
   - **Allow anonymous docker pull**: ✓ (for easier k8s usage) or ✗ (for security)
   - **Enable Docker V1 API**: ✗ (not needed)
4. Click **Create repository**

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

```bash
# Add registry.k8s-demo.de to Docker's insecure registries if not using HTTPS
# Or trust the Let's Encrypt certificate (should work automatically)

# Login to the registry
docker login registry.k8s-demo.de
# Username: admin (or create a new user in Nexus)
# Password: your-nexus-password
```

### Push Images

```bash
# Tag your image
docker tag demo-api:latest registry.k8s-demo.de/demo-api:latest

# Push to registry
docker push registry.k8s-demo.de/demo-api:latest

# List images in registry
curl -u admin:password https://registry.k8s-demo.de/v2/_catalog
```

### Pull Images from Kubernetes

#### Option 1: Anonymous Pull (if enabled)

No configuration needed! Just use the image:

```yaml
spec:
  containers:
    - name: demo-api
      image: registry.k8s-demo.de/demo-api:latest
```

#### Option 2: With Authentication

Create a Docker registry secret:

```bash
kubectl create secret docker-registry nexus-registry \
  --docker-server=registry.k8s-demo.de \
  --docker-username=admin \
  --docker-password=your-password \
  -n demo-api

# Use in deployment
kubectl patch serviceaccount default -n demo-api \
  -p '{"imagePullSecrets": [{"name": "nexus-registry"}]}'
```

Or add to deployment:

```yaml
spec:
  imagePullSecrets:
    - name: nexus-registry
  containers:
    - name: demo-api
      image: registry.k8s-demo.de/demo-api:latest
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

- **nexus.k8s-demo.de**: Nexus web UI (port 8081)
- **registry.k8s-demo.de**: Docker registry (port 5000)

Both use Let's Encrypt for TLS certificates.

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

1. **Check Nexus logs** for authentication errors
2. **Verify Docker registry** is configured in Nexus (port 5000)
3. **Check ingress** for registry.k8s-demo.de
4. **Test registry API**:
   ```bash
   curl https://registry.k8s-demo.de/v2/
   # Should return: {}
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
