# No-Deposit Rental Platform — Condensed Spec

URL: https://nodeposit.kubetest.uk  
Stack: Django 5.x · DRF · Keycloak 24 · oauth2-proxy · PostgreSQL 16 · Celery/Redis · S3

## Actors & Roles (Keycloak realm: `no-deposit`)

| Role | Responsibilities |
|---|---|
| `tenant` | Register, submit deposit application, retrieve guarantee certificate, manage payments |
| `landlord` | Validate guarantee, report damage claims, manage tenancy |
| `agent` | Review/approve applications, risk assessment, process claims, compliance |
| `admin` | Full platform access, Django admin |

Test users: `tenant1/Tenant1Pass!` · `landlord1/Landlord1Pass!` · `agent1/Agent1Pass!`

## Architecture

```
Browser → Traefik → oauth2-proxy (OIDC session) → Django app
                          ↑                              ↓
                    Keycloak (auth.kubetest.uk)     PostgreSQL
                    realm: no-deposit               (shared cluster DB)
```

- oauth2-proxy handles OIDC session; Django stays stateless (JWT only)
- All in k3s cluster on Hetzner; Flux GitOps from this repo

## URL Structure

| Path | Portal | Role |
|---|---|---|
| `/` | Landing page | all authenticated |
| `/tenant/` | Tenant dashboard | tenant |
| `/landlord/` | Landlord dashboard | landlord |
| `/agency/` | Agency dashboard | agent |
| `/admin/` | Django admin | admin |
| `/api/v1/` | REST API | role-scoped |
| `/api/docs/` | Swagger UI | all |
| `/health/` | Health check | public |

## Core Data Models

```
UserProfile         keycloak_sub, role, phone
Property            landlord_fk, address, rent_amount, status
RentalApplication   property_fk, tenant_profile_fk, status[pending/approved/rejected]
Guarantee           application_fk(1:1), certificate_number, valid_until, status[active/expired/claimed], document_url
DamageClaim         guarantee_fk, amount_claimed, evidence_urls, status[open/under_review/approved/rejected]
AuditLog            entity_type, entity_id, action, actor_id, actor_ip, timestamp  ← immutable
```

## Key API Endpoints (all JWT-secured)

```
POST   /api/v1/applications/              tenant: submit application
GET    /api/v1/applications/              tenant: own | agent: all
PATCH  /api/v1/applications/{id}/review/ agent: approve/reject
POST   /api/v1/guarantees/               agent: issue guarantee
GET    /api/v1/guarantees/{id}/validate/ landlord: check status
POST   /api/v1/claims/                   landlord: submit damage claim
POST   /api/v1/documents/upload/         tenant: KYC upload → S3 pre-signed URL
POST   /api/v1/payments/intent/          payment intent (Stripe)
GET    /api/v1/me/export/                GDPR data export
DELETE /api/v1/me/                       GDPR erasure
```

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Django 5.x + DRF |
| Auth | mozilla-django-oidc → Keycloak |
| OIDC proxy | oauth2-proxy v7.6.0 |
| Database | PostgreSQL 16 (shared cluster) |
| Storage | Hetzner Object Storage / MinIO + django-storages |
| Task queue | Celery + Redis |
| Email | AWS SES |
| PDF | WeasyPrint |
| Payments | Stripe (SEPA + card) |
| CI | GitHub Actions → GHCR image push → Flux |
| Monitoring | Prometheus/Grafana (existing) + Sentry |

## Security Requirements

- JWT validation on every API request against Keycloak JWKS (no server-side sessions on API)
- MFA enforced for `agent` and `admin` roles in Keycloak
- KYC documents in S3 only, accessed via 15-min pre-signed URLs; no PII in logs
- All secrets SOPS/age encrypted in git
- AuditLog immutable: every status change records actor_id, timestamp, IP
- Keycloak admin behind Tailscale only (`keycloak-admin.tail55277.ts.net`)
- Rate limiting: 100 req/min user, 10 req/min anon, 5 applications/hour/user

## Deployment Phases (bd issues created)

1. **Phase 1** — Django foundation: scaffold, Dockerfile, CI, k8s manifests, Flux image automation
2. **Phase 2** — OIDC + role-based access: mozilla-django-oidc, permission classes, portal views
3. **Phase 3** — Data models: UserProfile, Property, Application, Guarantee, DamageClaim, AuditLog, migrations
4. **Phase 4** — REST API: DRF router, OpenAPI, application/guarantee/claim/payment endpoints
5. **Phase 5** — Documents: S3 storage, KYC upload, PDF certificate generation (WeasyPrint)
6. **Phase 6** — Async: Redis/Celery deployment, email notifications (SES)
7. **Phase 7** — Security: rate limiting, MFA, GDPR endpoints, OWASP checklist
8. **Phase 8** — Observability: prometheus metrics, Sentry, structured JSON logging
9. **Phase 9** — Testing: full e2e login tests, pytest-django unit tests, CI smoke test

## Current State

- oauth2-proxy healthy, login works for all 3 test users ✓
- Keycloak `no-deposit` realm with audience mapper ✓
- nginx serving placeholder landing page at `/` ✓
- Portal paths `/tenant/`, `/landlord/`, `/agency/` return 404 (nginx, not Django yet)
- 47 bd issues created covering all phases above
