# homelab-demo

## Stack context
- **no-deposit app**: Django 5.x + DRF · Keycloak 24 (realm: `no-deposit`) · oauth2-proxy · PostgreSQL 16 · Celery/Redis
- Live at: https://nodeposit.kubetest.uk — auth at https://auth.kubetest.uk
- k3s on Hetzner, GitOps via Flux from this repo

## Key paths
- `apps/base/no-deposit/` — Kubernetes manifests for no-deposit stack
- `docs/no-deposit-spec.md` — full spec: models, roles, API endpoints, URL structure
- `scripts/test-login.py` — headless OIDC end-to-end login test
- `.sops.yaml` — SOPS age key config; encrypt with `sops -e -i <file>`
- `tasks/lessons.md` — hard-won corrections; update after any mistake

## Common commands
```bash
# Flux
flux reconcile kustomization flux-system --with-source
flux reconcile kustomization apps --with-source
flux logs --kind=Kustomization --name=apps

# kubectl
kubectl -n no-deposit get pods
kubectl -n no-deposit logs deploy/nginx-deployment
kubectl -n no-deposit describe ingress

# SOPS
sops -e -i apps/base/no-deposit/some-secret.yaml
sops -d apps/base/no-deposit/oauth2-proxy-secret.yaml

# Test login (requires playwright)
python scripts/test-login.py

# Beads task tracker
bd list
bd show <id>
bd done <id>
```

## Flux CD conventions
- **Never** run `kubectl apply` directly — all changes go through Git + Flux
- Manifests in `apps/base/no-deposit/` are managed by Flux; edit files, commit, push
- Secrets must be SOPS-encrypted before commit (regex: `^(data|stringData)$`)

## Keycloak hard rules (see docs/keycloak-admin-security-notes.md)
- `KC_HOSTNAME` = hostname only, no scheme, no trailing slash (e.g. `auth.kubetest.uk`)
- Do NOT set `KC_HOSTNAME_ADMIN` — causes admin UI to break with Tailscale operator
- Keycloak must be exposed via `Ingress`, not `LoadBalancer`
- Remove `X-Frame-Options: DENY` (frameDeny) from Traefik middleware for Keycloak
- Audience mapper required on client config for oauth2-proxy JWT validation

## OIDC / oauth2-proxy rules
- Cookie secret: raw 32 bytes, not base64 (`openssl rand -hex 16` NOT `openssl rand -base64 32`)
- Flag is `--email-domain` (not `--email-domains`) in v7.x
- Keycloak `/realms/<name>` endpoint must be on the public ingress

## Django app structure (no-deposit)
- Roles: `tenant`, `landlord`, `agent`, `admin` — sourced from Keycloak JWT claims
- Test users: `tenant1/Tenant1Pass!` · `landlord1/Landlord1Pass!` · `agent1/Agent1Pass!`
- oauth2-proxy handles sessions; Django uses JWT only (stateless)
- New app code goes in `apps/no-deposit/` (to be created in Phase 1)

## Code style
- Python: ruff for lint + format (`uvx ruff check` / `uvx ruff format`)
- No raw `kubectl apply` — hooks will catch this
