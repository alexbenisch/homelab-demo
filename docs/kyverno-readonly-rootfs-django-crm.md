---
title: "Kyverno PSS — readOnlyRootFilesystem fix for django-crm"
author: "Alex Benisch"
date: 2026-06-19
geometry: "margin=1.5cm"
papersize: a4
---

# Kyverno PSS — readOnlyRootFilesystem fix for django-crm

Changes made to bring `django-crm` into compliance with the `require-readonly-rootfs` rule
in `infrastructure/base/kyverno/policy-pss-restricted.yaml`.

---

## Context

The Kyverno `ClusterPolicy` added to this repo enforces (currently in Audit mode)
that all containers set `readOnlyRootFilesystem: true`. Five deployments in the cluster had
`readOnlyRootFilesystem: false` explicitly set. `django-crm` was the first to fix because
it already had a `/tmp` emptyDir volume in place, suggesting the fix was started but not completed.

---

## 1. Root cause — entrypoint patched files on the root filesystem at startup

**Problem:** `docker/django-crm/entrypoint.sh` used `sed -i` and a Python script to patch
`/app/webcrm/settings.py` at container startup. Specifically it rewrote:

- `ALLOWED_HOSTS`
- `SECRET_KEY`
- `MIDDLEWARE` (to insert WhiteNoise)
- `CSRF_TRUSTED_ORIGINS`
- `DATABASES` (entire block, via a regex-based Python script writing to `/tmp/db_patch.py` then executing it)

These are all writes to the image's root filesystem. Setting `readOnlyRootFilesystem: true`
would cause the container to crash immediately on the first `sed -i` call, before Django
even starts.

**Why it existed:** `settings_docker.py` was present in the repo but was never wired up
as `DJANGO_SETTINGS_MODULE`. It was a standalone file that re-declared `BASE_DIR` and
omitted `INSTALLED_APPS`, `MIDDLEWARE`, URL config, and everything else from the upstream
django-crm `settings.py`. It could not be used as-is, so the entrypoint patched the
upstream file instead.

---

## 2. Fix — settings_docker.py as a proper override module

**File:** `docker/django-crm/settings_docker.py`

Added `from webcrm.settings import *` as the first statement. This imports `INSTALLED_APPS`,
`MIDDLEWARE`, `ROOT_URLCONF`, `BASE_DIR`, `SECRET_KEY`, and everything else from the upstream
cloned settings, then the rest of the file overrides only what differs for production:

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` — from env vars
- `DATABASES` — PostgreSQL from env vars
- `MIDDLEWARE` — WhiteNoise inserted after `SecurityMiddleware` programmatically
- `STATIC_ROOT`, `STATICFILES_STORAGE` — WhiteNoise-compatible static file config
- `LOGGING` — console-only output

Removed `from pathlib import Path` and the manual `BASE_DIR = Path(__file__).resolve().parent.parent`
since `BASE_DIR` is now imported from the upstream settings.

---

## 3. Fix — DJANGO_SETTINGS_MODULE set in the image

**File:** `docker/django-crm/Dockerfile`

Added `DJANGO_SETTINGS_MODULE=webcrm.settings_docker` to the `ENV` block. This means:

- The build-time `collectstatic` step uses the correct settings (static files collected
  to `STATIC_ROOT = BASE_DIR / 'staticfiles'` at build time, served by WhiteNoise at runtime)
- The runtime gunicorn `CMD` inherits it automatically
- No manual wiring needed in the entrypoint or the Kubernetes manifest (though the manifest
  also sets it explicitly for visibility — see step 4)

---

## 4. Fix — entrypoint.sh stripped of all file-patching

**File:** `docker/django-crm/entrypoint.sh`

Removed all five sed/file-patching blocks. With `settings_docker.py` as the active settings
module, every value those patches set is already read from the environment variables that the
Kubernetes deployment provides.

Also removed the `collectstatic` call at the end of the entrypoint. Static files are
collected during `docker build` (the `RUN python manage.py collectstatic` layer in the
Dockerfile). Running it again at startup is redundant and would fail silently on a
read-only filesystem anyway.

What remains in the entrypoint: PostgreSQL readiness wait, `migrate`, `loaddata`, superuser
creation, and `exec "$@"`.

---

## 5. Fix — deployment manifest

**File:** `apps/base/django-crm/deployment.yaml`

Two changes:

1. `readOnlyRootFilesystem: false` → `readOnlyRootFilesystem: true`
2. Added env var `DJANGO_SETTINGS_MODULE: webcrm.settings_docker` (explicit for
   observability; the Dockerfile `ENV` already sets it in the image)

The existing `/tmp` emptyDir volume mount (already present before these changes) covers
any temp file writes from `migrate`, `loaddata`, and the superuser shell command.

---

## Deployment note

This change requires a new image build before the manifest change takes effect.
The old image's entrypoint still does `sed -i` on startup — if the new manifest
(with `readOnlyRootFilesystem: true`) is deployed against the old image, the container
will crashloop. Build and push first:

```bash
docker build -t ghcr.io/alexbenisch/django-crm:<sha> docker/django-crm/
docker push ghcr.io/alexbenisch/django-crm:<sha>
# update image tag in deployment.yaml, then commit and push
```

---

## Remaining deployments with readOnlyRootFilesystem: false

| Deployment | Namespace | Status |
|---|---|---|
| `tested-django` | tested-django | Next — same pattern, missing `/tmp` emptyDir |
| `cluster-dashboard` | cluster-dashboard | Needs runtime investigation (custom image) |
| `demo-api` | demo-api | Scaled to 0, lower urgency |
| `demo-django` | demo-django | Scaled to 0, lower urgency |
