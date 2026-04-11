# Keycloak Admin UI — Tailscale-Only Access

## Status

The two-instance plan was evaluated and **abandoned**. Running two Keycloak instances
against a shared PostgreSQL database is an unsupported configuration: each instance
has its own Infinispan cache, cache invalidation is not coordinated, and Keycloak
maintainers explicitly warn against it. The approach has known data consistency risks.

## Correct Approach

Single Keycloak instance with two separate ingresses and `KC_HOSTNAME_ADMIN`:

```
Public internet
    └── auth.kubetest.uk  (Traefik Ingress)
            ├── /realms/demo    ← app OIDC (Django, API)
            └── /resources      ← static assets
            (no /admin, no /realms/master)

Tailscale
    └── keycloak-admin.tail55277.ts.net  (Tailscale Ingress)
            └── /  (all paths)  ← admin console + admin REST API

Shared:
    └── one keycloak deployment with:
            KC_HOSTNAME=https://auth.kubetest.uk
            KC_HOSTNAME_ADMIN=https://keycloak-admin.tail55277.ts.net
```

## How It Works

When `KC_HOSTNAME_ADMIN` is set, Keycloak embeds that URL as `authServerUrl` in the
admin console page — so the JS makes all admin REST API calls to the Tailscale host,
not to the public host. The OIDC auth flow for the admin console also runs entirely
through the Tailscale ingress.

The public ingress exposes only `/realms/demo` and `/resources`. The admin console
(`/admin/`) is never reachable from the public internet.

## Configuration

`KC_HOSTNAME` must be a full URL (not hostname-only) when `KC_HOSTNAME_ADMIN` is also
set. Both values include the scheme.

```yaml
- name: KC_HOSTNAME
  value: https://auth.kubetest.uk
- name: KC_HOSTNAME_ADMIN
  value: https://keycloak-admin.tail55277.ts.net
```

## Validation

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

## Why the Earlier Approach Appeared to Break

An earlier attempt with `KC_HOSTNAME_ADMIN` failed because `KC_HOSTNAME` had a scheme
prefix (`https://auth.kubetest.uk`) AND `KC_HOSTNAME_ADMIN` was also set — this
caused a double-scheme OIDC issuer bug. The root cause was the KC_HOSTNAME scheme,
not KC_HOSTNAME_ADMIN itself. With KC_HOSTNAME as a full URL, both env vars work
correctly together.

See also: `docs/keycloak-tailscale-operator.md` for all hard-won configuration rules.
