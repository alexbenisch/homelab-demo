# Cluster Dashboard

A comprehensive Kubernetes cluster monitoring dashboard built with FastAPI. Displays real-time cluster information including nodes, pods, services, ingresses, and storage across all namespaces.

## Features

- **📦 Nodes Overview**: Status, resources, regions, instance types
- **🚀 Pods Monitoring**: All pods grouped by namespace with status
- **🌐 Ingresses & Domains**: All domains and IP addresses
- **🔌 Services**: Internal and external services with endpoints
- **💾 Storage**: Persistent volumes and their status
- **📊 Real-time Statistics**: Live cluster metrics
- **🎨 Modern UI**: Clean, responsive dashboard
- **🔄 Auto-refresh**: Updates every 30 seconds

## Use Cases

Perfect for:
- Monitoring homelab clusters
- Testing cloud provider infrastructure (AWS EKS, Azure AKS, GCP GKE, OCI OKE)
- Quick cluster health checks
- Learning Kubernetes resource relationships
- Comparing clusters across different providers

## Screenshots

The dashboard shows:
- Node information with cloud provider details (region, zone, instance type)
- All running pods organized by namespace
- Ingress routes with domains and IP addresses
- Services with their endpoints
- Persistent volume claims and status

## Local Development

### Prerequisites

- Python 3.11+
- uv package manager
- kubectl configured with cluster access

### Setup

```bash
cd cluster-dashboard

# Install dependencies
uv pip install -e .

# Run locally (reads from ~/.kube/config)
python src/main.py
```

Visit `http://localhost:8000`

### Docker

```bash
# Build
docker build -t cluster-dashboard:latest .

# Run (mount kubeconfig)
docker run -p 8000:8000 \
  -v ~/.kube/config:/home/appuser/.kube/config:ro \
  cluster-dashboard:latest
```

## Kubernetes Deployment

### Build and Load Image

```bash
# Build image
cd cluster-dashboard
docker build -t cluster-dashboard:latest .

# Load to all cluster nodes
docker save cluster-dashboard:latest | ssh alex@ctrl 'sudo k3s ctr images import -'
docker save cluster-dashboard:latest | ssh alex@wrkr1 'sudo k3s ctr images import -'
# Repeat for additional workers
```

### Deploy with Flux

```bash
# Add to staging kustomization
# Edit apps/staging/kustomization.yaml and add cluster-dashboard

# Commit and push
git add apps/base/cluster-dashboard apps/staging/cluster-dashboard cluster-dashboard/
git commit -m "Add cluster dashboard application"
git push

# Reconcile with Flux
flux reconcile kustomization apps --with-source
```

### Verify Deployment

```bash
# Check deployment
kubectl get pods -n cluster-dashboard
kubectl get svc -n cluster-dashboard
kubectl get ingress -n cluster-dashboard

# Check logs
kubectl logs -n cluster-dashboard -l app=cluster-dashboard

# Access via port-forward (for testing)
kubectl port-forward -n cluster-dashboard svc/cluster-dashboard 8000:80
```

## Access

- **URL**: https://cluster-dashboard.tail55277.ts.net (Tailscale VPN only)
- **Local**: http://localhost:8000 (port-forward for testing)

The dashboard is secured with Tailscale and only accessible when connected to the Tailnet. This provides secure, authenticated access without exposing the dashboard to the public internet.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard web UI |
| `GET /health` | Health check |
| `GET /api/cluster` | Cluster information JSON |
| `GET /api/nodes` | All nodes JSON |
| `GET /api/pods` | All pods grouped by namespace JSON |
| `GET /api/services` | All services JSON |
| `GET /api/ingresses` | All ingresses JSON |
| `GET /api/pvcs` | All PVCs JSON |

## RBAC Permissions

The dashboard requires read-only access to cluster resources:

- Nodes (status, capacity, labels)
- Pods (all namespaces)
- Services and Endpoints
- Ingresses
- Persistent Volume Claims
- Namespaces
- Deployments, ReplicaSets, StatefulSets, DaemonSets

Additionally, the Tailscale sidecar requires:
- Secret management (create, get, update, patch) for state storage
- Event creation for debugging

The ServiceAccount, ClusterRole, and Role are defined in `rbac.yaml`.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Port to listen on |
| `LOG_LEVEL` | `info` | Logging level |
| `ENVIRONMENT` | `development` | Environment name |

### Kubernetes

The app automatically detects if it's running inside Kubernetes and uses in-cluster config. Otherwise, it uses `~/.kube/config`.

## Cloud Provider Information

The dashboard extracts cloud provider metadata from node labels:

- **Instance Type**: `node.kubernetes.io/instance-type`
- **Region**: `topology.kubernetes.io/region`
- **Zone**: `topology.kubernetes.io/zone`

This works across AWS EKS, Azure AKS, GCP GKE, OCI OKE, and other managed Kubernetes services.

## Testing on Multiple Providers

Use this dashboard to compare clusters across different cloud providers:

```bash
# AWS EKS
aws eks update-kubeconfig --name my-cluster --region us-east-1
kubectl port-forward -n cluster-dashboard svc/cluster-dashboard 8000:80

# Azure AKS
az aks get-credentials --resource-group myRG --name myCluster
kubectl port-forward -n cluster-dashboard svc/cluster-dashboard 8001:80

# GCP GKE
gcloud container clusters get-credentials my-cluster --zone us-central1-a
kubectl port-forward -n cluster-dashboard svc/cluster-dashboard 8002:80
```

Compare:
- Node instance types and pricing
- Resource allocation patterns
- Network configuration
- Storage class availability
- Regional distribution

## Troubleshooting

### Dashboard shows no data

```bash
# Check RBAC permissions
kubectl auth can-i list nodes --as=system:serviceaccount:cluster-dashboard:cluster-dashboard
kubectl auth can-i list pods --as=system:serviceaccount:cluster-dashboard:cluster-dashboard

# Check pod logs
kubectl logs -n cluster-dashboard -l app=cluster-dashboard

# Verify service account
kubectl get sa -n cluster-dashboard
kubectl get clusterrolebinding cluster-dashboard-viewer
```

### Pod fails to start

```bash
# Check events
kubectl describe pod -n cluster-dashboard -l app=cluster-dashboard

# Check image
kubectl get pod -n cluster-dashboard -o jsonpath='{.items[0].spec.containers[0].image}'

# Test image locally
docker run -p 8000:8000 cluster-dashboard:latest
```

### Cannot access dashboard

```bash
# Check Tailscale sidecar is running
kubectl get pods -n cluster-dashboard
kubectl logs -n cluster-dashboard -l app=cluster-dashboard -c tailscale

# Verify Tailscale connection
kubectl logs -n cluster-dashboard -l app=cluster-dashboard -c tailscale | grep "Startup complete"

# Check that certificate was issued
kubectl logs -n cluster-dashboard -l app=cluster-dashboard -c tailscale | grep "got cert"

# Port-forward for local testing (bypasses Tailscale)
kubectl port-forward -n cluster-dashboard svc/cluster-dashboard 8000:80
```

## Development

### Project Structure

```
cluster-dashboard/
├── src/
│   ├── main.py              # FastAPI application
│   ├── templates/
│   │   └── dashboard.html   # Dashboard UI
│   └── static/
│       └── css/
│           └── style.css    # Styles
├── pyproject.toml           # Dependencies
├── Dockerfile               # Container image
└── README.md
```

### Adding New Features

Edit `src/main.py` to add new data collection functions and API endpoints.

### Styling

The dashboard uses CSS variables for easy theming. Edit `src/static/css/style.css`.

## Security

- **Tailscale Authentication**: Only accessible via private VPN
- **No Public Exposure**: Not accessible from the internet
- **Encrypted Connection**: Automatic HTTPS with Tailscale certificates
- Runs as non-root user (UID 1000)
- Read-only cluster access (no write permissions to cluster resources)
- Resource limits configured
- Health checks enabled
- Auto-refresh prevents stale data

## Performance

- Lightweight Python application
- Efficient Kubernetes API queries
- In-memory caching (30-second page refresh)
- Minimal resource usage (128Mi RAM)

## Comparison with Other Dashboards

| Feature | Cluster Dashboard | Kubernetes Dashboard | Lens |
|---------|-------------------|---------------------|------|
| **Installation** | Single pod | Complex setup | Desktop app |
| **RBAC** | Read-only | Admin access | Configurable |
| **UI** | Simple, focused | Feature-rich | Full IDE |
| **Resource Usage** | 128Mi | 256Mi+ | Desktop only |
| **Cloud Info** | Built-in | Limited | Plugin |
| **Learning** | Great for beginners | Advanced | Professional |

## Resources

- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)

## License

Part of the homelab-demo repository.
