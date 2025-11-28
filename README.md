# Homelab Demo

A GitOps-powered Kubernetes homelab running on k3s with Flux CD. This repository demonstrates modern cloud-native practices including infrastructure as code, encrypted secrets management, and automated deployments.

## 🏗️ Infrastructure

- **Kubernetes**: k3s cluster (1 control plane + workers)
- **GitOps**: Flux CD for automated deployments
- **Ingress**: Traefik with automatic Let's Encrypt certificates
- **DNS**: External-DNS with Hetzner webhook for automated DNS management
- **Secrets**: SOPS with age encryption for secure secret management
- **Domain**: k8s-demo.de

## 📦 Deployed Applications

### [Linkding](apps/base/linkding/)
**Bookmark Manager** - Self-hosted bookmark management application

- **URL**: https://linkding.k8s-demo.de
- **Image**: `sissbruecker/linkding:1.31.0`
- **Storage**: 5Gi persistent volume
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Bookmark collection and organization
  - Tag-based categorization
  - Full-text search
  - Browser extensions support

### [Wallabag](apps/base/wallabag/)
**Read-it-Later Service** - Save and organize articles for reading

- **URL**: https://wallabag-1.tail55277.ts.net (Tailnet-only)
- **Image**: `wallabag/wallabag:latest`
- **Storage**: 5Gi persistent volume
- **Access**: Private (Tailscale sidecar)
- **Features**:
  - Article extraction and storage
  - Offline reading
  - Mobile apps available
  - RSS feed generation

### [Demo API](apps/base/demo-api/)
**FastAPI REST API** - Portable Python application for testing across platforms

- **URL**: https://demo-api.k8s-demo.de
- **Built with**: FastAPI + uv package manager
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Health and readiness probes
  - Metrics endpoint
  - System info endpoint (shows environment details)
  - Request echo for debugging proxies
  - Auto-generated API documentation at `/docs`

### [Demo Django](apps/base/demo-django/)
**Django Web Application** - Learning Django deployment with GitOps workflows

- **URL**: https://demo-django.k8s-demo.de
- **Built with**: Django 5.0 + Gunicorn + WhiteNoise + uv package manager
- **Image**: `ghcr.io/alexbenisch/demo-django:latest` (GitHub Container Registry)
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Health and readiness probes for Kubernetes
  - System info endpoint for debugging
  - Django admin interface
  - Automated CI/CD with GitHub Actions
  - SOPS-encrypted secrets for Django secret key
  - Static file serving with WhiteNoise
  - Production-ready WSGI server (Gunicorn)

### [Tested Django](apps/base/tested-django/)
**Django Application with Comprehensive Testing** - Demonstrating Django's integrated unit testing in CI/CD

- **URL**: https://tested-django.k8s-demo.de
- **Built with**: Django 5.0 + PostgreSQL + Gunicorn + WhiteNoise + uv package manager
- **Image**: `ghcr.io/alexbenisch/tested-django:latest` (GitHub Container Registry)
- **Database**: PostgreSQL 16 with persistent storage (5Gi)
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Comprehensive Django unittest-based test suite (20+ tests)
  - GitHub Actions CI/CD with automated testing
  - Django's native TestCase framework
  - PostgreSQL database with automatic backups
  - Test-first development example
  - Health and readiness probes
  - Production-ready deployment after tests pass

### [Cluster Dashboard](apps/base/cluster-dashboard/)
**Kubernetes Monitoring Dashboard** - Real-time cluster monitoring and visualization

- **URL**: https://cluster-dashboard.tail55277.ts.net (Tailnet-only)
- **Image**: `cluster-dashboard:latest` (local build)
- **Built with**: FastAPI + Kubernetes Python Client + uv
- **Access**: Private (Tailscale sidecar)
- **Features**:
  - Live cluster metrics and statistics
  - Nodes overview with cloud provider details (region, zone, instance type)
  - All pods grouped by namespace
  - Ingress routes with domains and IP addresses
  - Services with endpoints
  - Persistent volume claims and status
  - Auto-refresh every 30 seconds
  - Read-only RBAC permissions
  - Secured with Tailscale authentication
  - Perfect for homelab monitoring and multi-cloud testing

### [WordPress](apps/base/wordpress/)
**Content Management System** - Popular CMS for websites and blogs

- **URL**: https://wordpress.k8s-demo.de
- **Image**: `wordpress:6.4-apache`
- **Database**: MySQL 8.0 with persistent storage (5Gi)
- **Storage**: 5Gi persistent volume for WordPress content
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Full WordPress CMS with MySQL backend
  - Persistent storage for content and uploads
  - Automatic Let's Encrypt SSL certificates
  - Health and readiness probes
  - SOPS-encrypted database credentials

## 🚀 Getting Started

### Prerequisites

- k3s cluster with kubectl access
- Flux CLI installed
- SOPS with age key configured
- GitHub repository access

### Deploy an Application

All applications are managed via GitOps with Flux:

```bash
# 1. Add your app to apps/base/ directory
# 2. Add to staging kustomization
vim apps/staging/kustomization.yaml

# 3. Commit and push
git add apps/
git commit -m "Add new application"
git push

# 4. Trigger Flux reconciliation
flux reconcile kustomization apps --with-source

# 5. Verify deployment
kubectl get pods -n your-app-namespace
```

## 🔐 Secrets Management

Secrets are encrypted with SOPS using age encryption:

```bash
# Create a secret
cat > apps/base/myapp/secret.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secret
stringData:
  PASSWORD: my-secret-password
EOF

# Encrypt with SOPS
sops -e -i apps/base/myapp/secret.yaml

# Commit (now safely encrypted)
git add apps/base/myapp/secret.yaml
git commit -m "Add encrypted secret"
git push

# Flux automatically decrypts and applies!

# To view/edit an encrypted secret locally:
sops apps/base/myapp/secret.yaml

# To decrypt to stdout:
sops -d apps/base/myapp/secret.yaml
```

The age public key is configured in `.sops.yaml`.
**Note**: You need the age private key in `~/.config/sops/age/keys.txt` to decrypt secrets locally.

## 🌐 DNS Management

DNS records are automatically managed via external-dns with Hetzner webhook:

- Add the annotation to your Ingress: `external-dns.alpha.kubernetes.io/hostname: myapp.k8s-demo.de`
- Push to git and reconcile with Flux
- DNS record is automatically created in Hetzner DNS

## 📚 Documentation

- [Deployment Guide](docs/deployment.md) - Detailed deployment instructions
- [Testing Deployments](docs/testing-deployments.md) - How to test deployments
- [Persistent Storage](docs/persistent-storage.md) - Storage configuration
- [Tailnet-Only Apps](docs/tailnet-only-apps.md) - Private apps with Tailscale
- [Wallabag Deployment Test](docs/wallabag-deployment-test.md) - Wallabag setup guide

## 🏗️ Repository Structure

```
homelab-demo/
├── apps/
│   ├── base/              # Base application manifests
│   │   ├── cluster-dashboard/ # Cluster dashboard app
│   │   ├── demo-api/      # Demo FastAPI application
│   │   ├── demo-django/   # Demo Django application
│   │   ├── linkding/      # Linkding bookmark manager
│   │   ├── tested-django/ # Tested Django application
│   │   ├── wallabag/      # Wallabag read-it-later
│   │   └── wordpress/     # WordPress CMS
│   └── staging/           # Staging overlays
│       └── kustomization.yaml
├── infrastructure/
│   ├── base/              # Infrastructure components
│   │   └── external-dns/  # External DNS with Hetzner
│   └── staging/
├── clusters/              # Flux cluster configuration
│   └── staging/
├── cluster-dashboard/     # Cluster dashboard source code
│   ├── src/
│   ├── Dockerfile
│   └── pyproject.toml
├── demo-api/              # Demo API source code
│   ├── src/
│   ├── Dockerfile
│   └── pyproject.toml
├── demo-django/           # Demo Django source code
│   ├── src/
│   ├── Dockerfile
│   └── pyproject.toml
├── tested-django/         # Tested Django source code
│   ├── src/
│   ├── Dockerfile
│   └── pyproject.toml
├── docs/                  # Documentation
├── cloud-init/            # Cloud-init configs for nodes
└── .sops.yaml            # SOPS encryption config
```

## 🔧 Maintenance

### Update Flux

```bash
flux check --pre
flux install --export > clusters/staging/flux-system/gotk-components.yaml
git commit -am "Update Flux components"
git push
```

### View Flux Status

```bash
# Overall status
flux get all

# Specific resources
flux get kustomizations
flux get helmreleases

# Logs
flux logs --follow --level=error
```

### Backup

Important data to backup:

- Persistent volumes (linkding, wallabag)
- SOPS age private key (`~/.config/sops/age/keys.txt`)
- Kubernetes secrets (if not in git)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This is a personal homelab demo repository. Use at your own risk.

## 🔗 Resources

- [Flux Documentation](https://fluxcd.io/docs/)
- [k3s Documentation](https://docs.k3s.io/)
- [SOPS Documentation](https://github.com/mozilla/sops)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [External DNS](https://github.com/kubernetes-sigs/external-dns)
