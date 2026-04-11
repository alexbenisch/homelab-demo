# Keycloak + Tailscale Operator: Configuration Rules

Confirmed working 2026-04-11. Apply all of these from the start.

## 1. KC_HOSTNAME and KC_HOSTNAME_ADMIN — hostname only, no scheme

Keycloak prepends `https://` to both values. Passing a full URL causes double-scheme
(`https://https://...`) in `authServerUrl`, `authUrl`, CSP `frame-src`, and OIDC
issuer URLs. Always hostname-only — with or without KC_HOSTNAME_ADMIN:

```yaml
- name: KC_HOSTNAME
  value: auth.kubetest.uk
- name: KC_HOSTNAME_ADMIN
  value: keycloak-admin.tail55277.ts.net
```

## 2. Use KC_HOSTNAME_ADMIN to route admin console through Tailscale

When `KC_HOSTNAME_ADMIN` is set, the admin console page embeds it as `authUrl`.
The OIDC auth redirect goes through the Tailscale hostname. `authServerUrl` remains
KC_HOSTNAME (the public hostname) — the 3p-cookies iframe and OIDC login flow both
need this. The admin REST API (`/admin/`) is served via the Tailscale ingress.

Do NOT run two separate Keycloak instances against a shared PostgreSQL database —
Infinispan cache is per-instance with no coordination. Unsupported configuration.

## 3. Expose these paths on the public Traefik ingress

```yaml
- path: /realms/demo    # public OIDC for app clients
- path: /realms/master  # 3p-cookies iframe + admin console OIDC login flow
- path: /resources      # static assets
```

Do NOT expose `/admin` — admin REST API must only be reachable via the Tailscale
ingress. The admin console login flow uses `/realms/master` on the public hostname
(authServerUrl = KC_HOSTNAME) but all admin API calls go through Tailscale (authUrl =
KC_HOSTNAME_ADMIN).

## 4. Use Tailscale Ingress, not LoadBalancer

`type: LoadBalancer, loadBalancerClass: tailscale` does raw TCP passthrough — TLS
fails because the app speaks plain HTTP.

```yaml
# correct
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    tailscale.com/hostname: keycloak-admin
spec:
  ingressClassName: tailscale
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: keycloak
                port:
                  number: 8080
  tls:
    - hosts:
        - keycloak-admin
```

## 5. Remove frameDeny from Traefik middleware

`frameDeny: true` sets `X-Frame-Options: DENY` on all responses. This blocks
Keycloak's `3p-cookies/step1.html` iframe used by the JS adapter for session state.

Symptom: 5-minute hang, then `Timeout when waiting for 3rd party check iframe
message` in browser console.

```yaml
spec:
  headers:
    # frameDeny: true  ← remove this, Keycloak manages frame options per-endpoint
    contentTypeNosniff: true
    browserXssFilter: true
```

## Validation

```bash
# Admin blocked publicly
curl -sI https://auth.kubetest.uk/admin/master/console/        # → 404

# Demo realm OIDC issuer clean (no double scheme)
curl -s https://auth.kubetest.uk/realms/demo/.well-known/openid-configuration \
  | python3 -m json.tool | grep issuer
# → "issuer": "https://auth.kubetest.uk/realms/demo"

# login-status-iframe accepts Tailscale origin
curl -sv "https://auth.kubetest.uk/realms/master/protocol/openid-connect/login-status-iframe.html/init?client_id=security-admin-console&origin=https%3A%2F%2Fkeycloak-admin.tail55277.ts.net"
# → HTTP/2 204

# Full browser check (headless) — 0 failed requests means login page is clean
python3 scripts/browser-debug.py https://keycloak-admin.tail55277.ts.net/admin/master/console/ 15
```

Note: `scripts/browser-debug.py` may report one `FAILED` on `/init` — this is
Playwright closing the browser while a background poll is still in-flight. Not a real
error if the same URL returned 204 earlier in the same run.
