# Keycloak Two-Instance Plan: Tailscale-Only Admin UI

## Goal

Run two Keycloak instances against one PostgreSQL database so the admin
console is completely isolated on the Tailscale network, with no admin
paths exposed on the public internet.

## Architecture

```
Public internet
    └── auth.kubetest.uk  (Traefik)
            └── keycloak (deployment)         KC_HOSTNAME=auth.kubetest.uk
                    ├── /realms/demo           ← app OIDC (Django, API)
                    └── /resources             ← static assets
                    (no /admin, no /realms/master)

Tailscale
    └── keycloak-admin.tail55277.ts.net  (Tailscale Ingress)
            └── keycloak-admin (deployment)   KC_HOSTNAME=keycloak-admin.tail55277.ts.net
                    └── /  (all paths)         ← admin console + admin REST API

Shared:
    └── keycloak-postgres (single PostgreSQL)  ← both instances read/write here
```

## Files to Change

| File | Action |
|---|---|
| `apps/base/keycloak/admin-deployment.yaml` | Create |
| `apps/base/keycloak/admin-service.yaml` | Create |
| `apps/base/keycloak/service-admin-tailscale.yaml` | Modify — point backend to `keycloak-admin` service |
| `apps/base/keycloak/ingress.yaml` | Modify — remove `/admin` and `/realms/master` paths |
| `apps/base/keycloak/kustomization.yaml` | Modify — add two new files |

## Step 1 — Create the admin deployment

New file `apps/base/keycloak/admin-deployment.yaml`:

- Same image (`quay.io/keycloak/keycloak:24.0`), same `args: [start-dev]`
- Reuse existing secrets (`keycloak-credentials`, `keycloak-postgres-secret`)
- Reuse existing PostgreSQL service (`keycloak-postgres:5432`)
- `KC_HOSTNAME=keycloak-admin.tail55277.ts.net`
- `KC_HTTP_ENABLED=true`, `KC_PROXY_HEADERS=xforwarded`
- No `KC_HOSTNAME_ADMIN`, no `KC_HOSTNAME_STRICT`
- Smaller resources — admin only, low traffic

## Step 2 — Create the admin service

New file `apps/base/keycloak/admin-service.yaml`:

- `name: keycloak-admin`
- `selector: app: keycloak-admin`
- Port 8080

## Step 3 — Point the Tailscale ingress at the admin service

Modify `apps/base/keycloak/service-admin-tailscale.yaml`:

- Change `backend.service.name` from `keycloak` → `keycloak-admin`

## Step 4 — Clean up the public ingress

Modify `apps/base/keycloak/ingress.yaml` — remove paths no longer needed publicly:

- Remove `/admin` — admin REST API stays Tailscale-only
- Remove `/realms/master` — admin OIDC now lives on `keycloak-admin.tail55277.ts.net`

Public ingress should only expose:
- `/realms/demo`
- `/resources`
- `/realms/demo/protocol/openid-connect/token` (rate-limited ingress)

## Step 5 — Update kustomization.yaml

Add `admin-deployment.yaml` and `admin-service.yaml` to the resources list.

## Step 6 — Validate

```bash
# Public instance: only demo realm reachable
curl https://auth.kubetest.uk/realms/demo/.well-known/openid-configuration  # 200
curl https://auth.kubetest.uk/admin/master/console/                          # 404
curl https://auth.kubetest.uk/realms/master/.well-known/openid-configuration # 404

# Admin instance (must be on Tailscale)
curl https://keycloak-admin.tail55277.ts.net/admin/master/console/           # 200

# authServerUrl in the admin console page must be the Tailscale hostname
curl -s https://keycloak-admin.tail55277.ts.net/admin/master/console/ \
  | python3 -c "import sys,re; m=re.search(r'<script id=\"environment\".*?</script>', sys.stdin.read(), re.DOTALL); print(m.group())" \
  | grep authServerUrl
# → "authServerUrl": "https://keycloak-admin.tail55277.ts.net"
```

## Cache Caveat

Both instances share PostgreSQL but each has its own local Infinispan
cache. Changes made via the admin console write to PostgreSQL immediately,
but the public instance's cache won't reflect them until the cache expires
or the pod restarts.

**Workaround (demo):** After making admin changes, run:

```bash
kubectl rollout restart deployment/keycloak -n keycloak
```

**Proper fix (later):** Configure JGroups `KUBE_PING` so both instances
form a Keycloak cluster — cache invalidation then happens automatically.
Requires one extra RBAC resource and a few env vars on both deployments.
