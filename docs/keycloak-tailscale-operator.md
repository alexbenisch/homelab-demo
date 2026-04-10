# Keycloak + Tailscale Operator: Configuration Rules

Lessons from ~2 days of debugging. Apply all of these from the start.

## 1. KC_HOSTNAME — hostname only, no scheme

```yaml
- name: KC_HOSTNAME
  value: auth.kubetest.uk        # correct
# value: https://auth.kubetest.uk  # wrong — causes https://https//... in OIDC issuer URLs
```

## 2. Do not use KC_HOSTNAME_ADMIN

Setting a separate admin hostname creates a split-domain problem. The admin console JS embeds `authServerUrl` (KC_HOSTNAME) and `authUrl` (request hostname) separately. With a dedicated admin hostname, the admin REST API calls and OIDC auth flows end up on different domains, causing a 5-minute hang and broken UI. Without KC_HOSTNAME_ADMIN, Keycloak sets the authUrl dynamically from the request — this works correctly for both the Tailscale ingress and the public ingress.

## 3. Expose these paths on the public Traefik ingress

```yaml
- path: /realms/demo                  # public OIDC for app clients
- path: /realms/master                # admin console OIDC discovery + auth flow
- path: /admin                        # admin REST API (console breaks without this)
- path: /resources                    # static assets
```

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
