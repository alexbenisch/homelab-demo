# Keycloak + Tailscale Operator: Configuration Rules

Lessons from ~2 days of debugging. Apply all of these from the start.

## 1. KC_HOSTNAME and KC_HOSTNAME_ADMIN — use full URLs when both are set

When `KC_HOSTNAME_ADMIN` is also configured, both must be full URLs:

```yaml
- name: KC_HOSTNAME
  value: https://auth.kubetest.uk               # full URL required when KC_HOSTNAME_ADMIN is set
- name: KC_HOSTNAME_ADMIN
  value: https://keycloak-admin.tail55277.ts.net
```

If running with a single hostname and no KC_HOSTNAME_ADMIN, hostname-only works:
```yaml
- name: KC_HOSTNAME
  value: auth.kubetest.uk        # hostname-only is fine for single-ingress setup
```

## 2. Use KC_HOSTNAME_ADMIN to isolate admin behind Tailscale

When `KC_HOSTNAME_ADMIN` is set, Keycloak embeds it as `authServerUrl` in the admin
console page. All admin REST API calls and the admin OIDC flow go to the admin
hostname — the public hostname never sees admin traffic.

An earlier attempt without KC_HOSTNAME_ADMIN exposed `/admin` on the public ingress to
make the console work — this defeats the Tailscale security goal. Use KC_HOSTNAME_ADMIN
instead.

Do NOT run two separate Keycloak instances against a shared PostgreSQL database —
Infinispan cache is per-instance with no coordination. Unsupported configuration.

## 3. Expose only these paths on the public Traefik ingress

```yaml
- path: /realms/demo                  # public OIDC for app clients
- path: /resources                    # static assets
```

Do NOT expose `/admin` or `/realms/master` publicly — those are admin-only paths,
accessible only via the Tailscale ingress.

## 4. Use Tailscale Ingress, not LoadBalancer

`type: LoadBalancer, loadBalancerClass: tailscale` does raw TCP passthrough — TLS fails because the app speaks plain HTTP.

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

`frameDeny: true` sets `X-Frame-Options: DENY` on all responses. This blocks Keycloak's `3p-cookies/step1.html` iframe used by the JS adapter for session state checking.

Symptom: 5-minute hang, then `Timeout when waiting for 3rd party check iframe message` in browser console.

```yaml
spec:
  headers:
    # frameDeny: true  ← remove this, Keycloak manages frame options per-endpoint
    contentTypeNosniff: true
    browserXssFilter: true
```

## Validation

```bash
# OIDC issuer should be clean (no double scheme)
curl -s https://auth.kubetest.uk/realms/master/.well-known/openid-configuration | python3 -m json.tool | grep issuer
# → "issuer": "https://auth.kubetest.uk/realms/master"

# 3p-cookies iframe must not have X-Frame-Options: deny
curl -sv https://auth.kubetest.uk/realms/master/protocol/openid-connect/3p-cookies/step1.html 2>&1 | grep -i x-frame
# → (no output — header must be absent)
```
