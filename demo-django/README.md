# Demo Django - Learning Django Deployment with GitOps

A simple Django application designed for learning GitOps deployment workflows to your homelab Kubernetes cluster. This project demonstrates modern cloud-native practices with automated CI/CD via GitHub Actions and Flux CD.

## Features

- **Django 5.0** with modern best practices
- **Gunicorn** WSGI server for production
- **WhiteNoise** for efficient static file serving
- **Health & Readiness** probes for Kubernetes
- **System info** endpoint for debugging
- **GitOps deployment** with Flux CD
- **Automated CI/CD** with GitHub Actions
- **Container registry** integration with GitHub Container Registry

## Access

Once deployed:
- **URL**: `https://demo-django.k8s-demo.de`
- **Admin**: `https://demo-django.k8s-demo.de/admin/`
- **Health**: `https://demo-django.k8s-demo.de/health/`
- **Info**: `https://demo-django.k8s-demo.de/info/`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Home page with app information |
| `GET /health/` | Health check (liveness probe) |
| `GET /ready/` | Readiness check |
| `GET /info/` | System and environment information |
| `GET /admin/` | Django admin interface |

## Local Development

### Prerequisites

- Python 3.11+
- [uv package manager](https://github.com/astral-sh/uv) (optional but recommended)

### Setup

```bash
# Navigate to the demo-django directory
cd demo-django

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
# OR with uv:
uv pip install -e .

# Navigate to src directory
cd src

# Run migrations
python manage.py migrate

# Create superuser (for admin access)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

The app will be available at `http://localhost:8000`

### Using Docker Locally

```bash
# Build the Docker image
cd demo-django
docker build -t demo-django:dev .

# Run the container
docker run -p 8000:8000 \
  -e DJANGO_SECRET_KEY=local-dev-secret \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  -e DJANGO_DEBUG=True \
  demo-django:dev
```

## GitOps Deployment Workflow

This project uses a complete GitOps workflow:

### 1. Code Changes

Make changes to the Django application:

```bash
cd demo-django/src/core
# Edit views.py, models.py, templates, etc.
git add .
git commit -m "Add new feature"
git push origin main
```

### 2. Automated Build (GitHub Actions)

When you push to main, GitHub Actions automatically:
1. Builds the Docker image
2. Pushes to GitHub Container Registry at `ghcr.io`
3. Tags with `latest` and the git commit SHA

The workflow file: `.github/workflows/demo-django.yaml`

### 3. Automated Deployment (Flux CD)

Flux CD monitors the Kubernetes manifests in `apps/staging/demo-django/`:
1. Detects changes in the Git repository
2. Applies updates to the cluster
3. Pulls the new image from the registry
4. Performs rolling updates with zero downtime

### 4. Verification

```bash
# Check Flux status
flux get kustomizations

# Check pod status
kubectl get pods -n demo-django

# View logs
kubectl logs -n demo-django -l app=demo-django -f

# Check rollout status
kubectl rollout status deployment/demo-django -n demo-django
```

## GitHub Configuration

The CI/CD pipeline uses GitHub Container Registry (ghcr.io), which is automatically configured when using GitHub Actions:

- No additional secrets needed - uses built-in `GITHUB_TOKEN`
- Images are pushed to `ghcr.io/<owner>/demo-django`
- Requires "packages: write" permission (already configured in workflow)

## Kubernetes Deployment

### Prerequisites

1. k3s cluster with kubectl access
2. Flux CD installed and configured
3. Traefik ingress controller (comes with k3s)
4. External-DNS with Hetzner for automatic DNS

### Manual Deploy (if not using Flux)

```bash
# Apply Kubernetes manifests
kubectl apply -k apps/staging/demo-django

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment/demo-django -n demo-django

# Check status
kubectl get all -n demo-django
```

### Trigger Flux Reconciliation

```bash
# Force Flux to sync immediately
flux reconcile kustomization apps --with-source

# Monitor Flux
flux logs --follow
```

## Configuration

### Environment Variables

The deployment uses these environment variables (configured in `apps/base/demo-django/deployment.yaml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | From secret | Django secret key (encrypted with SOPS) |
| `DJANGO_ALLOWED_HOSTS` | `demo-django.k8s-demo.de,...` | Allowed hostnames |
| `DJANGO_DEBUG` | `False` | Debug mode (always False in production) |
| `ENVIRONMENT` | `production` | Environment name |

### Secrets Management

The Django secret key should be encrypted with SOPS:

```bash
# Generate a new secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Edit the secret
vim apps/base/demo-django/secret.yaml

# Encrypt with SOPS
sops -e -i apps/base/demo-django/secret.yaml

# Commit and push
git add apps/base/demo-django/secret.yaml
git commit -m "Update Django secret key"
git push
```

## Updating the Application

### Code Updates

```bash
# 1. Make your changes
vim demo-django/src/core/views.py

# 2. Commit and push
git add demo-django/
git commit -m "Update homepage view"
git push origin main

# 3. GitHub Actions builds and pushes automatically

# 4. Update Kubernetes deployment to trigger rollout
kubectl set image deployment/demo-django \
  demo-django=ghcr.io/<owner>/demo-django:main-$(git rev-parse --short HEAD) \
  -n demo-django

# OR wait for Flux to sync (if using image automation)
```

### Configuration Updates

```bash
# 1. Update Kubernetes manifests
vim apps/base/demo-django/deployment.yaml

# 2. Commit and push
git add apps/base/demo-django/
git commit -m "Update deployment configuration"
git push origin main

# 3. Flux applies changes automatically
# Or manually trigger:
flux reconcile kustomization apps --with-source
```

## Monitoring and Debugging

### View Logs

```bash
# All pods
kubectl logs -n demo-django -l app=demo-django --tail=100 -f

# Specific pod
kubectl logs -n demo-django <pod-name> -f

# Previous container (if crashed)
kubectl logs -n demo-django <pod-name> --previous
```

### Check Health

```bash
# From outside
curl https://demo-django.k8s-demo.de/health/

# From inside cluster
kubectl exec -n demo-django -l app=demo-django -- \
  curl -s http://localhost:8000/health/
```

### Shell Access

```bash
# Get shell in running pod
kubectl exec -it -n demo-django <pod-name> -- /bin/sh

# Run Django management commands
kubectl exec -n demo-django <pod-name> -- \
  python manage.py showmigrations
```

### Common Issues

#### ImagePullBackOff

```bash
# Check GitHub Actions workflow to see if build succeeded
# Go to: https://github.com/your-repo/actions

# Verify image exists in GitHub Container Registry
# Go to: https://github.com/your-user?tab=packages
```

#### CrashLoopBackOff

```bash
# Check logs for errors
kubectl logs -n demo-django -l app=demo-django --tail=50

# Check events
kubectl describe pod -n demo-django -l app=demo-django

# Common causes:
# - Missing or invalid DJANGO_SECRET_KEY
# - Incorrect DJANGO_ALLOWED_HOSTS
# - Application errors in code
```

#### DNS Not Working

```bash
# Check external-dns logs
kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns

# Check ingress
kubectl get ingress -n demo-django
kubectl describe ingress demo-django -n demo-django

# Verify DNS record
dig demo-django.k8s-demo.de
```

## Development Workflow Example

Here's a complete workflow for adding a new feature:

```bash
# 1. Create feature branch (optional)
git checkout -b feature/new-endpoint

# 2. Add new view
cat >> demo-django/src/core/views.py << 'EOF'

@require_http_methods(["GET"])
def my_feature(request):
    return JsonResponse({'message': 'Hello from my feature!'})
EOF

# 3. Add URL route
echo "    path('my-feature/', views.my_feature, name='my-feature')," >> \
  demo-django/src/core/urls.py

# 4. Test locally
cd demo-django/src
python manage.py runserver

# 5. Commit and push
git add .
git commit -m "Add my-feature endpoint"
git push origin feature/new-endpoint

# 6. Create PR, review, merge to main

# 7. GitHub Actions builds automatically

# 8. Deploy to cluster (manual trigger or wait for Flux)
flux reconcile kustomization apps --with-source

# 9. Test in production
curl https://demo-django.k8s-demo.de/my-feature/
```

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Flux CD Documentation](https://fluxcd.io/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

## Next Steps

### Add Database

Replace SQLite with PostgreSQL:

1. Add PostgreSQL to your cluster
2. Update `DATABASES` in `settings.py`
3. Add database credentials to secrets
4. Run migrations

### Add Celery for Background Tasks

1. Add Redis to cluster
2. Configure Celery in Django
3. Create worker deployment
4. Add beat scheduler for periodic tasks

### Add Static File Storage

Configure S3-compatible storage for static files:

1. Add django-storages
2. Configure S3/MinIO
3. Update STATIC settings

### Add Monitoring

1. Add Prometheus metrics with django-prometheus
2. Configure Grafana dashboards
3. Set up alerts

## License

This is a demo/learning project. Use freely for educational purposes.
