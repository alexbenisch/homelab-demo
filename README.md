# Homelab Demo

A GitOps-powered Kubernetes homelab running on k3s with Flux CD. This repository demonstrates modern cloud-native practices including infrastructure as code, encrypted secrets management, and automated deployments.

## 🏗️ Infrastructure

- **Platform**: Hetzner Cloud (automated with Terraform via GitHub Actions)
- **Kubernetes**: k3s cluster (1 control plane + 2 workers)
- **GitOps**: Flux CD for automated deployments
- **Ingress**: Traefik with automatic Let's Encrypt certificates (DNS challenge via Cloudflare)
- **DNS**: External-DNS with Cloudflare for automated DNS management
- **Secrets**: SOPS with age encryption for secure secret management
- **Domains**: k8s-demo.de (Hetzner), kubetest.uk (Cloudflare)

### Infrastructure Deployment

The cluster infrastructure is fully automated with Terraform and GitHub Actions:

- **[Terraform Setup Guide](terraform/README.md)** - Deploy/destroy infrastructure via GitHub workflows
- **[DNS Management](terraform/dns/README.md)** - Manage subdomains via GitHub Actions workflow
- **[Migration Guide](docs/migration-strategy.md)** - Migrate from old cluster to Terraform + new DNS API
- **Manual Setup** (legacy): [cloud-init/README.md](cloud-init/README.md)

> **📋 Migrating?** See the complete [Migration Strategy](docs/migration-strategy.md) for moving from the current cluster to a Terraform-managed cluster with the new Hetzner Cloud DNS API.
>
> **🌐 Managing DNS?** Use the [DNS Management Workflow](terraform/dns/README.md) to create/update subdomains via GitHub Actions.

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

### [Grafana](apps/base/grafana/)
**Monitoring and Observability Platform** - Metrics visualization and dashboarding

- **URL**: https://grafana.k8s-demo.de
- **Image**: `grafana/grafana:latest`
- **Storage**: 10Gi persistent volume for dashboards and data
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Metrics visualization and dashboarding
  - Data source integrations (Prometheus, Loki, etc.)
  - Customizable dashboards
  - Automatic Let's Encrypt SSL certificates
  - SOPS-encrypted admin credentials
  - Ready for cluster monitoring setup

### [Django CRM](apps/base/django-crm/)
**Customer Relationship Management** - Open-source CRM for managing contacts, leads, and opportunities

- **URL**: https://immomo.kubetest.uk
- **Image**: `ghcr.io/alexbenisch/django-crm:latest` (GitHub Container Registry)
- **Database**: PostgreSQL 16 with persistent storage (5Gi)
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Contact and account management
  - Lead tracking and conversion
  - Opportunity pipeline management
  - Task and activity tracking
  - Team collaboration features
  - Django admin interface
  - SOPS-encrypted credentials

---

## 🏨 Hotel Management Package

A complete self-hosted solution for hotel operations, deployed on the `kubetest.uk` domain.

**Landing Page**: https://hotelpackage.kubetest.uk

### [Hotel Package Landing Page](apps/base/hotel-package/)
**Marketing Landing Page** - Showcase for the hotel management suite

- **URL**: https://hotelpackage.kubetest.uk
- **Image**: `nginx:alpine`
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Modern responsive design
  - Links to all suite applications
  - Feature highlights for each app
  - Contact information

### [Paperless-ngx](apps/base/paperless-ngx/)
**Document Management System** - Transform paper chaos into searchable digital archives

- **URL**: https://paperless.kubetest.uk
- **Image**: `ghcr.io/paperless-ngx/paperless-ngx:latest`
- **Database**: PostgreSQL 16 + Redis
- **Storage**: 10Gi (data) + 20Gi (media) + 5Gi (consume)
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Automatic document scanning & OCR
  - Smart tagging & categorization
  - Full-text search across all documents
  - Multi-language OCR support (English + German)
  - Secure document storage

### [Nextcloud](apps/base/nextcloud/)
**File Sync & Collaboration Platform** - Your private cloud for files, calendars, and collaboration

- **URL**: https://nextcloud.kubetest.uk
- **Image**: `nextcloud:29-apache`
- **Database**: PostgreSQL 16 + Redis
- **Storage**: 50Gi persistent volume
- **Access**: Public (via Traefik ingress)
- **Features**:
  - File sync across all devices
  - Shared calendars & contacts
  - Real-time document collaboration
  - Guest sharing for external partners
  - WebDAV, CalDAV, CardDAV support

### [Mattermost](apps/base/mattermost/)
**Team Communication Platform** - Secure messaging for hotel staff coordination

- **URL**: https://mattermost.kubetest.uk
- **Image**: `mattermost/mattermost-team-edition:9.11`
- **Database**: PostgreSQL 16
- **Storage**: 10Gi persistent volume
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Real-time messaging & channels
  - File sharing & search
  - Mobile apps for staff on the go
  - Plugin ecosystem for integrations
  - Team organization features

### [QloApps](apps/base/qlo-apps/)
**Hotel Booking System** - Complete reservation and booking management

- **URL**: https://qloapps.kubetest.uk
- **Image**: `webkul/qloapps_docker:latest`
- **Database**: Internal MySQL (bundled in container)
- **Storage**: 15Gi persistent volume
- **Access**: Public (via Traefik ingress)
- **Features**:
  - Online booking engine
  - Room & rate management
  - Multi-channel distribution
  - Guest management & reporting
  - Payment gateway integrations

---

## 🚀 Getting Started

### Prerequisites

- k3s cluster with kubectl access
- Flux CLI installed
- SOPS with age key configured
- GitHub repository access

### Adding New Applications - Checklist

Before creating manifests for a new application, review existing applications to understand the cluster's patterns and requirements:

**Infrastructure Patterns to Follow:**
1. **Storage**: Default storage class is `local-path` - do NOT specify `storageClassName` in PVCs
2. **Ingress Controller**: Cluster uses `traefik` (not nginx)
3. **Required Ingress Annotations**:
   - `external-dns.alpha.kubernetes.io/hostname: your-app.k8s-demo.de` (for automatic DNS)
   - `traefik.ingress.kubernetes.io/router.entrypoints: web,websecure`
   - `traefik.ingress.kubernetes.io/router.tls.certresolver: letsencrypt` (for automatic TLS)
4. **Secrets**: All secrets must be encrypted with SOPS before committing
5. **Namespace**: Each app should have its own namespace defined in `namespace.yaml`

**Reference Examples:**
- Simple app with public access: `apps/base/linkding/`
- App with database: `apps/base/wordpress/`
- App with CI/CD: `apps/base/demo-django/` or `apps/base/tested-django/`
- Private app with Tailscale: `apps/base/wallabag/` or `apps/base/cluster-dashboard/`

**Pre-deployment Checklist:**
- [ ] Reviewed existing apps for patterns
- [ ] PVC does not specify storageClassName (uses default `local-path`)
- [ ] Ingress uses Traefik annotations (not nginx)
- [ ] Ingress has `external-dns.alpha.kubernetes.io/hostname` annotation
- [ ] Secrets are encrypted with SOPS
- [ ] Added app to `apps/staging/kustomization.yaml`

### Deploy an Application

Follow these steps to deploy a new application to the cluster. All applications are managed via GitOps with Flux CD.

#### Step 1: Create Base Manifests

Create a new directory under `apps/base/` with the following files:

```bash
mkdir -p apps/base/myapp

# Create namespace
cat > apps/base/myapp/namespace.yaml <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: myapp
EOF

# Create deployment
cat > apps/base/myapp/deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
EOF

# Create service
cat > apps/base/myapp/service.yaml <<EOF
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: myapp
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
  selector:
    app: myapp
EOF

# Create ingress with required annotations
cat > apps/base/myapp/ingress.yaml <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.k8s-demo.de
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    traefik.ingress.kubernetes.io/router.tls.certresolver: letsencrypt
spec:
  rules:
    - host: myapp.k8s-demo.de
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 8080
EOF

# Create PVC (if needed) - DO NOT specify storageClassName
cat > apps/base/myapp/pvc.yaml <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myapp-storage
  namespace: myapp
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
EOF

# Create secret
cat > apps/base/myapp/secret.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: myapp-credentials
  namespace: myapp
type: Opaque
stringData:
  admin-password: changeme123
EOF

# Create kustomization.yaml
cat > apps/base/myapp/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: myapp

resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
  - ingress.yaml
  - pvc.yaml
  - secret.yaml
EOF
```

#### Step 2: Encrypt Secrets with SOPS

```bash
# Encrypt the secret file
sops --encrypt --in-place apps/base/myapp/secret.yaml

# Verify encryption
cat apps/base/myapp/secret.yaml | grep ENC
```

#### Step 3: Create Staging Overlay

```bash
mkdir -p apps/staging/myapp

cat > apps/staging/myapp/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base/myapp
EOF
```

#### Step 4: Add to Staging Kustomization

```bash
# Edit apps/staging/kustomization.yaml and add your app to the resources list
vim apps/staging/kustomization.yaml

# Add this line to the resources section:
#  - myapp
```

#### Step 5: Commit and Push

```bash
# Stage all changes
git add apps/

# Commit with descriptive message
git commit -m "Add myapp application

- Add deployment with health probes
- Configure Traefik ingress with Let's Encrypt TLS
- Add external-dns annotation for automatic DNS
- Configure SOPS-encrypted credentials
- Add staging overlay
"

# Push to remote
git push
```

#### Step 6: Trigger Flux Reconciliation

```bash
# Trigger Flux to sync from git
flux reconcile kustomization apps --with-source

# Expected output:
# ✔ applied revision main@sha1:xxxxx
```

#### Step 7: Verify Deployment

```bash
# Check all resources
kubectl get all -n myapp

# Check pod status (should be Running)
kubectl get pods -n myapp

# Check PVC status (should be Bound)
kubectl get pvc -n myapp

# Check ingress (should have ADDRESS)
kubectl get ingress -n myapp

# Check pod logs
kubectl logs -n myapp -l app=myapp

# Verify DNS record was created (wait 1-2 minutes)
dig myapp.k8s-demo.de

# Test the application
curl https://myapp.k8s-demo.de
```

#### Step 8: Troubleshooting

If the pod is not starting:

```bash
# Describe the pod to see events
kubectl describe pod -n myapp -l app=myapp

# Check pod logs
kubectl logs -n myapp -l app=myapp --tail=50

# Check if PVC is pending
kubectl describe pvc -n myapp
```

If ingress is not working:

```bash
# Check ingress details
kubectl describe ingress -n myapp

# Verify external-dns created the record
kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns --tail=50 | grep myapp

# Check certificate status
kubectl get certificate -n myapp
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

### Cloudflare DNS (kubetest.uk)

DNS records for `kubetest.uk` are automatically managed via external-dns with Cloudflare:

1. Add the annotation to your Ingress: `external-dns.alpha.kubernetes.io/hostname: myapp.kubetest.uk`
2. Push to git and reconcile with Flux
3. DNS record is automatically created in Cloudflare

**Let's Encrypt certificates** are issued via DNS challenge (more reliable than TLS challenge):
- Traefik automatically creates DNS TXT records for validation
- Works even before DNS propagates
- Works with Cloudflare proxy enabled

### Deploying Apps to Cloudflare Domain

To deploy a new app on the `kubetest.uk` domain:

#### Step 1: Create Ingress with Cloudflare hostname

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  namespace: myapp
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.kubetest.uk
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    traefik.ingress.kubernetes.io/router.tls.certresolver: letsencrypt
spec:
  rules:
    - host: myapp.kubetest.uk
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 8080
```

#### Step 2: Deploy and verify

```bash
# Push changes
git add . && git commit -m "Add myapp" && git push

# Reconcile
flux reconcile kustomization apps --with-source

# Verify DNS record was created
dig myapp.kubetest.uk

# Check certificate status in Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik | grep myapp
```

### Hetzner DNS (k8s-demo.de) - Legacy

DNS records for `k8s-demo.de` are managed via external-dns with Hetzner webhook:

- Add the annotation to your Ingress: `external-dns.alpha.kubernetes.io/hostname: myapp.k8s-demo.de`
- Push to git and reconcile with Flux
- DNS record is automatically created in Hetzner DNS

**Note**: New apps should use the Cloudflare domain (`kubetest.uk`) for better Let's Encrypt support via DNS challenge.

## 📚 Documentation

### Infrastructure & Migration
- [Migration Quick Start](docs/migration-quick-start.md) - ⚡ 30-second overview and quick reference
- [Migration Strategy](docs/migration-strategy.md) - Complete guide for migrating to Terraform + new DNS API
- [Migration Checklist](docs/migration-checklist.md) - Step-by-step checklist for tracking progress
- [Migration Rollback](docs/migration-rollback.md) - Emergency rollback procedures

### DNS Management
- [DNS Workflow Quick Reference](docs/dns-workflow-quick-reference.md) - ⚡ Quick commands for creating subdomains
- [DNS Management Guide](terraform/dns/README.md) - Complete guide for Terraform DNS management

### Application Deployment
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
│   │   ├── django-crm/    # Django CRM application
│   │   ├── grafana/       # Grafana monitoring
│   │   ├── hotel-package/ # Hotel suite landing page
│   │   ├── linkding/      # Linkding bookmark manager
│   │   ├── mattermost/    # Team communication (Hotel Package)
│   │   ├── nextcloud/     # File sync & collaboration (Hotel Package)
│   │   ├── paperless-ngx/ # Document management (Hotel Package)
│   │   ├── qlo-apps/      # Hotel booking system (Hotel Package)
│   │   ├── tested-django/ # Tested Django application
│   │   ├── wallabag/      # Wallabag read-it-later
│   │   └── wordpress/     # WordPress CMS
│   └── staging/           # Staging overlays
│       └── kustomization.yaml
├── infrastructure/
│   ├── base/              # Infrastructure components
│   │   ├── external-dns/  # External DNS (Cloudflare)
│   │   └── traefik/       # Traefik config (Let's Encrypt DNS challenge)
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
├── terraform/             # Terraform infrastructure (GitHub Actions)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── cloud-init/        # Cloud-init templates for Terraform
│   └── dns/               # DNS management with Terraform
│       ├── main.tf
│       ├── variables.tf
│       └── README.md
├── cloud-init/            # Legacy manual cloud-init configs
├── .github/workflows/     # GitHub Actions workflows
│   ├── terraform.yml      # Terraform deployment workflow
│   └── dns-management.yml # DNS management workflow
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
