# OWASP Top 10 Security Checklist — no-deposit-app

Last reviewed: 2026-04-12

---

## A01 — Broken Access Control

| Control | Status | Where |
|---------|--------|-------|
| All API endpoints require JWT | DONE | `IsValidJWT` default permission class |
| Role checks per endpoint (tenant/landlord/agent/admin) | DONE | `HasRole`, `IsAgentOrAdmin` etc. in viewsets |
| Tenants can only see own applications | DONE | `get_queryset()` filters by `tenant=profile` |
| Landlords can only see own properties/claims | DONE | filtered by `property__landlord=profile` |
| GDPR deletion endpoint scoped to own data | DONE | `MeView.delete()` resolves profile from JWT |

## A02 — Cryptographic Failures

| Control | Status | Where |
|---------|--------|-------|
| JWT validated against Keycloak RS256 JWKS | DONE | `OAuthProxyJWTAuthentication` + PyJWKClient |
| HTTPS enforced at ingress (Traefik + cert-manager) | DONE | cluster ingress config |
| `SESSION_COOKIE_SECURE = True` in prod | DONE | `settings.py` |
| `CSRF_COOKIE_SECURE = True` in prod | DONE | `settings.py` |
| Secrets in SOPS-encrypted Kubernetes secrets | DONE | `django-secret.yaml` |
| No secrets in source code or ConfigMaps | DONE | all via env vars |
| Hetzner Object Storage bucket set to private | DONE | presigned URLs only |

## A03 — Injection

| Control | Status | Where |
|---------|--------|-------|
| All DB queries via Django ORM (no raw SQL) | DONE | all views use queryset API |
| Serializer validation on all input | DONE | DRF serializers with `is_valid(raise_exception=True)` |
| Evidence URLs stored as JSON, not executed | DONE | `DamageClaim.evidence_urls = JSONField` |

## A04 — Insecure Design

| Control | Status | Where |
|---------|--------|-------|
| Immutable audit log (no update/delete) | DONE | `AuditLog` overrides `save()`/`delete()` |
| Guarantee issued only for approved applications | DONE | viewset guard |
| Claims only against active guarantees | DONE | viewset guard |
| One guarantee per application enforced | DONE | `OneToOneField` + viewset guard |

## A05 — Security Misconfiguration

| Control | Status | Where |
|---------|--------|-------|
| `DEBUG = False` in production | DONE | env var, default False |
| `ALLOWED_HOSTS` set explicitly | DONE | `settings.py` |
| `SECURE_CONTENT_TYPE_NOSNIFF = True` | DONE | `settings.py` |
| `X_FRAME_OPTIONS = DENY` | DONE | `settings.py` |
| Admin UI behind Tailscale (no public access) | DONE | cluster network policy |
| Default Django admin only accessible with Django superuser | DONE | no superuser created in prod by default |

**TODO:** Verify Traefik adds `Strict-Transport-Security` header at ingress level.

## A06 — Vulnerable and Outdated Components

| Control | Status | Where |
|---------|--------|-------|
| Dependency versions pinned in `uv.lock` | DONE | `pyproject.toml` + `uv.lock` |
| GitHub Actions CI runs on each push | DONE | `.github/workflows/no-deposit.yaml` |

**TODO:** Add Dependabot or `uv lock --upgrade` cron to keep deps current.

## A07 — Identification and Authentication Failures

| Control | Status | Where |
|---------|--------|-------|
| All auth delegated to Keycloak (no homebrew auth) | DONE | oauth2-proxy + OIDC |
| JWT expiry validated (`ExpiredSignatureError`) | DONE | `OAuthProxyJWTAuthentication` |
| Token audience validated | DONE | `audience=settings.OIDC_RP_CLIENT_ID` in decode |
| MFA enforced for agent/admin roles | TODO | `homelab-demo-8qj` — Keycloak policy |
| Brute-force protection | DONE | Keycloak handles login; oauth2-proxy in front |

## A08 — Software and Data Integrity Failures

| Control | Status | Where |
|---------|--------|-------|
| Docker image built from pinned base (`python:3.12-slim`) | DONE | `Dockerfile` |
| Image pushed to private GHCR registry | DONE | CI workflow |
| Flux pulls image digest, not mutable tag | DONE | `flux-image-automation.yaml` |

## A09 — Security Logging and Monitoring Failures

| Control | Status | Where |
|---------|--------|-------|
| All business events recorded in `AuditLog` | DONE | all viewsets call `AuditLog.record()` |
| GDPR erasure events logged | DONE | `MeView.delete()` |
| Structured logging | TODO | `homelab-demo-0fn` (Phase 8) |
| Alerting / metrics | TODO | `homelab-demo-xuv`, `homelab-demo-cxm` (Phase 8) |

## A10 — Server-Side Request Forgery (SSRF)

| Control | Status | Where |
|---------|--------|-------|
| No user-controlled URLs fetched server-side | DONE | app does not fetch external URLs based on user input |
| JWKS endpoint is hardcoded, not user-supplied | DONE | `settings.py` |
| Presigned URL generation uses internal MinIO client only | DONE | `core/storage.py` |

---

## Open Items

1. **MFA for agent/admin** (`homelab-demo-8qj`) — enforce via Keycloak Authentication Policy
2. **HSTS at ingress** — verify Traefik middleware adds `Strict-Transport-Security: max-age=31536000`
3. **Dependabot** — automated dependency updates
4. **Structured logging** — Phase 8
