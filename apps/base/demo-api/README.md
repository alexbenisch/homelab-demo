# Demo API - Portable Python REST API

A simple, portable FastAPI application designed for testing across different platforms and environments. This app demonstrates cloud-native best practices and is perfect for learning different deployment platforms.

## Features

- **FastAPI** with automatic OpenAPI documentation
- **Health & Readiness** probes for Kubernetes
- **Metrics** endpoint for observability
- **Environment info** endpoint for debugging
- **Request echo** endpoint for testing proxies/load balancers
- **12-factor app** design for portability
- **uv package manager** for fast, reliable dependency management
- **Non-root container** with security best practices

## Access

- **URL**: `https://demo-api.k8s-demo.de`
- **API Documentation**: `https://demo-api.k8s-demo.de/docs`
- **Health Check**: `https://demo-api.k8s-demo.de/health`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Root endpoint with API information |
| `GET /docs` | Interactive API documentation (Swagger UI) |
| `GET /redoc` | Alternative API documentation (ReDoc) |
| `GET /health` | Health check (liveness probe) |
| `GET /ready` | Readiness check |
| `GET /metrics` | Basic metrics (requests, uptime) |
| `GET /info` | System and environment information |
| `GET /echo` | Echo request details (headers, client info) |
| `GET /version` | API version information |

## Local Development

### Prerequisites

- Python 3.11+
- [uv package manager](https://github.com/astral-sh/uv)

### Setup

```bash
# Navigate to the demo-api directory
cd demo-api

# Install dependencies with uv
uv pip install -e .

# Run the application
python src/main.py
```

The API will be available at `http://localhost:8000`

### Using Docker

```bash
# Build the Docker image
docker build -t demo-api:latest .

# Run the container
docker run -p 8000:8000 demo-api:latest

# Or with custom environment variables
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=debug \
  demo-api:latest
```

## Kubernetes Deployment

### Prerequisites

1. Kubernetes cluster with kubectl access
2. Ingress controller installed (nginx)
3. cert-manager for TLS certificates
4. DNS configured for `demo-api.k8s-demo.de`

### Build and Load Image

```bash
# Build the Docker image
cd demo-api
docker build -t demo-api:latest .

# Load into your cluster (for local clusters like k3s)
# Option 1: Direct pipe to k3s (fastest) - for multi-node clusters, import to ALL nodes
docker save demo-api:latest | ssh alex@ctrl 'sudo k3s ctr images import -'
docker save demo-api:latest | ssh alex@wrkr1 'sudo k3s ctr images import -'
# Repeat for additional worker nodes: wrkr2, wrkr3, etc.

# Option 2: Export once, then import to all nodes
docker save demo-api:latest -o /tmp/demo-api-latest.tar
scp /tmp/demo-api-latest.tar alex@ctrl:/tmp/
scp /tmp/demo-api-latest.tar alex@wrkr1:/tmp/
ssh alex@ctrl 'sudo k3s ctr images import /tmp/demo-api-latest.tar'
ssh alex@wrkr1 'sudo k3s ctr images import /tmp/demo-api-latest.tar'

# Option 3: Push to a registry (recommended for production/multi-node)
docker tag demo-api:latest your-registry/demo-api:latest
docker push your-registry/demo-api:latest
# Then update deployment.yaml image field with the registry path
```

### Deploy to Cluster

This deployment uses Flux CD for GitOps:

```bash
# Commit the changes
git add apps/base/demo-api apps/staging/demo-api apps/staging/kustomization.yaml
git commit -m "Add demo-api application"
git push

# Trigger Flux reconciliation
flux reconcile kustomization apps --with-source
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n demo-api

# Check service
kubectl get svc -n demo-api

# Check ingress
kubectl get ingress -n demo-api

# View logs
kubectl logs -n demo-api -l app=demo-api

# Test health check
kubectl exec -n demo-api -l app=demo-api -- curl http://localhost:8000/health
```

### Access the API

Once deployed and DNS is configured:

```bash
# Test the API
curl https://demo-api.k8s-demo.de/

# View API documentation in browser
open https://demo-api.k8s-demo.de/docs

# Check system info
curl https://demo-api.k8s-demo.de/info

# Test echo endpoint
curl https://demo-api.k8s-demo.de/echo
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Port the API listens on |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |
| `ENVIRONMENT` | `development` | Environment name (development, staging, production) |

### Kubernetes Environment Variables

The deployment automatically injects Kubernetes metadata:

- `POD_NAME`: Name of the pod
- `POD_NAMESPACE`: Namespace the pod is running in
- `POD_IP`: IP address of the pod
- `NODE_NAME`: Node the pod is scheduled on

These are visible in the `/info` endpoint.

## Use Cases

This demo API is designed to be deployed on multiple platforms for learning and testing:

1. **Kubernetes** (this deployment)
2. **Cloud Run** (Google Cloud)
3. **Lambda** (AWS)
4. **App Engine** (Google Cloud)
5. **Azure Container Apps**
6. **Fly.io**
7. **Railway**
8. **Render**

The `/info` endpoint helps verify the environment on each platform.

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -n demo-api -l app=demo-api

# Check logs
kubectl logs -n demo-api -l app=demo-api
```

### Image Pull Issues

If using a local image, ensure:
1. Image is built: `docker images | grep demo-api`
2. Image is loaded into cluster
3. `imagePullPolicy: IfNotPresent` is set in deployment.yaml

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n demo-api

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Verify cert-manager
kubectl get certificate -n demo-api
kubectl describe certificate demo-api-tls -n demo-api
```

### Health Checks Failing

```bash
# Test health endpoint from within the pod
kubectl exec -n demo-api -l app=demo-api -- curl -v http://localhost:8000/health

# Check if port is correct
kubectl get pod -n demo-api -l app=demo-api -o yaml | grep containerPort
```

## Development

### Adding New Endpoints

Edit `src/main.py` and add your endpoint:

```python
@app.get("/my-endpoint")
async def my_endpoint() -> Dict[str, Any]:
    return {"message": "Hello from my endpoint"}
```

Rebuild the Docker image and redeploy.

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests (when you add them)
pytest
```

## Security

- Runs as non-root user (UID 1000)
- Read-only root filesystem support
- No privilege escalation
- Resource limits configured
- TLS/HTTPS via cert-manager

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
