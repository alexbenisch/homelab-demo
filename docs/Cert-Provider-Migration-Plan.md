# Certificate Provider Migration Plan

## Overview

Migrate TLS certificate management from Traefik's built-in ACME to cert-manager with Hetzner DNS webhook for `k8s-demo.de` domains.

## Current State

### Certificate Resolvers (Traefik)

| Resolver | Challenge Type | DNS Provider | Status |
|----------|---------------|--------------|--------|
| `letsencrypt` | DNS-01 | Cloudflare | Broken for k8s-demo.de (DNS moved to Hetzner) |
| `letsencrypt-http` | HTTP-01 | N/A | Working (used for wp-ai-chatbot) |

### Certificates by Domain

| Domain | DNS Provider | Resolver | Renewal | Count |
|--------|--------------|----------|---------|-------|
| `*.kubetest.uk` | Cloudflare | letsencrypt | Working | 6 |
| `*.k8s-demo.de` | Hetzner | letsencrypt | **Broken** | 13 |
| `wp-ai-chatbot.k8s-demo.de` | Hetzner | letsencrypt-http | Working | 1 |

### Affected k8s-demo.de Services

1. dashboard.k8s-demo.de
2. demo-api.k8s-demo.de
3. demo-django.k8s-demo.de
4. docker.nexus.k8s-demo.de
5. docker-registry.k8s-demo.de
6. freelance-radar.k8s-demo.de
7. grafana.k8s-demo.de
8. linkding.k8s-demo.de
9. nexus.k8s-demo.de
10. prometheus.k8s-demo.de
11. registry.k8s-demo.de
12. tested-django.k8s-demo.de
13. wordpress.k8s-demo.de

## Target State

```
┌─────────────────────────────────────────────────────────────────┐
│                       cert-manager                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ClusterIssuers                                          │    │
│  │                                                          │    │
│  │  1. letsencrypt-hetzner (DNS-01, Hetzner webhook)       │    │
│  │     → For k8s-demo.de domains                           │    │
│  │                                                          │    │
│  │  2. letsencrypt-cloudflare (DNS-01, Cloudflare)         │    │
│  │     → For kubetest.uk domains (optional migration)      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Certificate Resources (per ingress)                     │    │
│  │  - Automatically created via ingress annotations         │    │
│  │  - Stored as Kubernetes Secrets                         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Migration Steps

### Phase 1: Install cert-manager

**Task:** `homelab-demo-i67`

```bash
# Add Helm repo
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager with CRDs
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true
```

Or via GitOps (recommended):

```yaml
# infrastructure/base/cert-manager/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: cert-manager
resources:
  - namespace.yaml
  - helmrelease.yaml
```

### Phase 2: Install Hetzner DNS Webhook for cert-manager

**Task:** `homelab-demo-du6`

> **IMPORTANT:** Hetzner has deprecated the old DNS Console API (`dns.hetzner.com`).
> Use the new Cloud API at `api.hetzner.cloud` with a Cloud API token.

```bash
# Install webhook for Hetzner DNS (cert-manager)
helm install cert-manager-webhook-hetzner \
  --namespace cert-manager \
  --set groupName=acme.hetzner.cloud \
  oci://ghcr.io/vadimkim/cert-manager-webhook-hetzner
```

Create Hetzner API secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: hetzner-dns-api-key
  namespace: cert-manager
type: Opaque
stringData:
  api-key: <HETZNER_CLOUD_API_TOKEN>  # Use SOPS encryption
```

### Phase 3: Create ClusterIssuer

**Task:** `homelab-demo-4k6`

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-hetzner
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: alexander.benisch@gmail.com
    privateKeySecretRef:
      name: letsencrypt-hetzner-account-key
    solvers:
      - dns01:
          webhook:
            groupName: acme.hetzner.cloud
            solverName: hetzner
            config:
              secretName: hetzner-dns-api-key
              zoneName: k8s-demo.de
              apiUrl: https://api.hetzner.cloud/v1
```

### Phase 4: Migrate Ingresses

**Task:** `homelab-demo-0mf`

**Before (Traefik certresolver):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wordpress
  annotations:
    traefik.ingress.kubernetes.io/router.tls.certresolver: letsencrypt
spec:
  rules:
    - host: wordpress.k8s-demo.de
      # ...
```

**After (cert-manager):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wordpress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-hetzner
spec:
  tls:
    - hosts:
        - wordpress.k8s-demo.de
      secretName: wordpress-tls
  rules:
    - host: wordpress.k8s-demo.de
      # ...
```

**Migration checklist:**

- [ ] linkding.k8s-demo.de
- [ ] demo-api.k8s-demo.de
- [ ] demo-django.k8s-demo.de
- [ ] tested-django.k8s-demo.de
- [ ] wordpress.k8s-demo.de
- [ ] grafana.k8s-demo.de
- [ ] prometheus.k8s-demo.de
- [ ] freelance-radar.k8s-demo.de
- [ ] nexus.k8s-demo.de
- [ ] registry.k8s-demo.de
- [ ] dashboard.k8s-demo.de
- [ ] docker.nexus.k8s-demo.de
- [ ] docker-registry.k8s-demo.de

### Phase 5: Cleanup

**Task:** `homelab-demo-4ms`

1. Remove Traefik Cloudflare certresolver config (keep for kubetest.uk or migrate too)
2. Delete old acme.json entries for k8s-demo.de
3. Remove hetzner-secret.yaml from Traefik (no longer needed)
4. Update documentation

## Rollback Plan

If migration fails:

1. Revert ingress annotations to Traefik certresolver
2. Existing certs in acme.json still valid until expiry
3. Use HTTP-01 challenge as temporary fallback

## Timeline

| Phase | Task | Priority |
|-------|------|----------|
| 1 | Install cert-manager | High |
| 2 | Install Hetzner webhook | High |
| 3 | Create ClusterIssuer | High |
| 4 | Migrate ingresses (one by one) | Medium |
| 5 | Cleanup | Low |

## Bonus: Automatic DNS Record Creation

### Add external-dns with Hetzner Webhook

**Task:** `homelab-demo-pc1`

Currently, DNS records for `k8s-demo.de` must be added manually. To automate this:

> **IMPORTANT:** Use the new Hetzner Cloud API (`api.hetzner.cloud`), NOT the deprecated `dns.hetzner.com`.

```yaml
# external-dns-hetzner-values.yaml
namespace: external-dns
policy: sync
provider:
  name: webhook
  webhook:
    image:
      repository: ghcr.io/mconfalonieri/external-dns-hetzner-webhook
      tag: v0.9.0
    env:
      - name: HETZNER_API_KEY
        valueFrom:
          secretKeyRef:
            name: hetzner-credentials
            key: api-key
      - name: USE_CLOUD_API
        value: "true"  # Required for api.hetzner.cloud
    livenessProbe:
      httpGet:
        path: /health
        port: http-webhook
    readinessProbe:
      httpGet:
        path: /ready
        port: http-webhook

domainFilters:
  - k8s-demo.de

extraArgs:
  - "--txt-prefix=reg-%{record_type}-"
```

Deploy:
```bash
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm install external-dns-hetzner external-dns/external-dns \
  -f external-dns-hetzner-values.yaml \
  -n external-dns
```

After this, any Ingress with `external-dns.alpha.kubernetes.io/hostname` annotation will automatically create DNS records.

## References

- [cert-manager Documentation](https://cert-manager.io/docs/)
- [cert-manager-webhook-hetzner](https://github.com/vadimkim/cert-manager-webhook-hetzner)
- [external-dns-hetzner-webhook](https://github.com/mconfalonieri/external-dns-hetzner-webhook)
- [Hetzner Cloud API - DNS](https://docs.hetzner.cloud/reference/cloud#dns)
- [Hetzner Community Tutorial](https://community.hetzner.com/tutorials/howto-k8s-traefik-certmanager)

## Related Tasks

- `homelab-demo-i67` - Install cert-manager in cluster
- `homelab-demo-du6` - Add cert-manager Hetzner DNS webhook
- `homelab-demo-4k6` - Create ClusterIssuer for Hetzner DNS-01
- `homelab-demo-0mf` - Migrate 13 k8s-demo.de ingresses to cert-manager
- `homelab-demo-4ms` - Remove legacy Traefik Cloudflare certresolver for k8s-demo.de
- `homelab-demo-pc1` - Add external-dns with Hetzner webhook for k8s-demo.de
- `homelab-demo-5zh` - Fix Terraform DNS config (related)
