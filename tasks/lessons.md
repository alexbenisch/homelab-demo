# Lessons Learned

Hard-won corrections and non-obvious decisions. Update after any mistake.

---

## OIDC / oauth2-proxy

**oauth2-proxy cookie secret must be raw 32 bytes, not base64**
- Wrong: `openssl rand -base64 32` → produces base64-encoded string, rejected
- Right: `openssl rand -hex 16` → produces 32 hex chars (32 bytes)

**Flag is `--email-domain` (singular) in oauth2-proxy v7.x**
- `--email-domains` (plural) does not exist in v7.x, causes silent failure
- Right: `--email-domain=*` or `--email-domain=kubetest.uk`

---

## Keycloak

**KC_HOSTNAME must be hostname only — no scheme, no path, no trailing slash**
- Wrong: `https://auth.kubetest.uk` → breaks redirect URIs
- Right: `auth.kubetest.uk`

**Do not set KC_HOSTNAME_ADMIN**
- Setting it causes admin UI to be unreachable via Tailscale operator
- Leave unset; KC_HOSTNAME covers both

**Audience mapper required on Keycloak client for oauth2-proxy JWT validation**
- Without it, the `aud` claim in the JWT does not match the client ID
- Add an "Audience" mapper to the client → Dedicated scope or hardcoded audience

**Keycloak /realms/<name> must be on the public ingress**
- oauth2-proxy (running in-cluster) cannot reach KC via internal-only path
- Ensure the OIDC discovery URL is reachable from inside the cluster

---

## Ingress / Traefik

**Keycloak must be exposed via Ingress, not LoadBalancer**
- Tailscale operator handles routing; LoadBalancer bypasses it

**Remove frameDeny from Traefik middleware for Keycloak**
- `X-Frame-Options: DENY` breaks the Keycloak admin console embedded views
- Either remove the middleware from Keycloak's ingress or set `SAMEORIGIN`

---

## Flux CD

**Never use kubectl apply directly — always go through Git + Flux**
- Direct applies get overwritten by the next reconcile
- If you need to test a manifest: `kubectl apply --dry-run=client -f <file>` only
