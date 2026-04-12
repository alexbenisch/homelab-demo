# Django on Kubernetes — Deployment Lessons

Errors encountered and fixed during the first real deployment of the no-deposit Django app.
Each entry has the symptom, root cause, and fix so we don't repeat it.

---

## 1. Ruff lint failures on migration files (E501)

**Symptom:** CI fails with `E501 Line too long` in `*/migrations/0001_initial.py`.

**Cause:** Auto-generated migration files have very long lines that `ruff format` won't rewrite
because they are not "owned" code.

**Fix:** Add a per-file ignore in `pyproject.toml`:
```toml
[tool.ruff.lint.per-file-ignores]
"*/migrations/*.py" = ["E501"]
```

---

## 2. Dockerfile apt-get install exit code 100 (WeasyPrint deps)

**Symptom:** Docker build fails on `apt-get install libcairo2 libffi8 libgdk-pixbuf2.0-0 ...`
with `exit code: 100`.

**Cause:** `libffi8` is already installed in `python:3.12-slim` (Python links against it).
`libgdk-pixbuf2.0-0` was renamed to `libgdk-pixbuf-2.0-0` in Debian Bookworm.

**Fix:** Simplify to just what WeasyPrint 60+ actually needs at runtime:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
```

---

## 3. Celery worker CrashLoopBackOff — `celery` not found in PATH

**Symptom:** Celery worker pod starts then crashes: `exec: "celery": executable file not found in $PATH`.

**Cause:** The Dockerfile multi-stage build only copied `gunicorn` from the builder stage,
not the `celery` binary.

**Fix:** Add `celery` to the COPY list:
```dockerfile
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=builder /usr/local/bin/celery /usr/local/bin/celery
```

---

## 4. Django health probe returns 400 — ALLOWED_HOSTS rejects pod IP

**Symptom:** Readiness/liveness probes fail with HTTP 400. Pod never becomes Ready.

**Cause:** Kubernetes kubelet sends HTTP probes using the pod's IP as the `Host` header.
Django's `ALLOWED_HOSTS` doesn't include pod IPs, so it rejects with 400.

**Fix:** Add an explicit `Host` header to the probe matching a value already in `ALLOWED_HOSTS`:
```yaml
readinessProbe:
  httpGet:
    path: /health/
    port: 8000
    httpHeaders:
      - name: Host
        value: no-deposit-django.no-deposit.svc.cluster.local
```

---

## 5. Pods in ImagePullBackOff — GHCR image is private

**Symptom:** All pods stuck in `ImagePullBackOff`. Event: `failed to authorize: 403 Forbidden`.

**Cause:** The container image on GHCR is private. No `imagePullSecrets` was configured on the
pod spec.

**Fix (two steps):**
1. Create a `docker-registry` secret in the namespace:
   ```bash
   kubectl create secret docker-registry ghcr-credentials \
     --namespace no-deposit \
     --docker-server=ghcr.io \
     --docker-username=<github-user> \
     --docker-password=<github-pat> \
     --docker-email=<email>
   ```
2. Reference it in every Deployment that pulls from GHCR:
   ```yaml
   spec:
     imagePullSecrets:
       - name: ghcr-credentials
   ```

---

## 6. Infinite recursion in DRF authentication → 500 on all API endpoints

**Symptom:** Every authenticated API request returns 500. Traceback shows `authenticate()` calling
itself recursively until Python hits the recursion limit.

**Cause:** `OAuthProxyJWTAuthentication.authenticate()` returned `(request.user, ...)`. In DRF,
`request.user` is a lazy property that calls `_authenticate()` when accessed — which calls
`authenticate()` again — infinite loop.

**Fix:** Return the underlying Django `HttpRequest`'s user instead:
```python
# WRONG — triggers DRF's lazy _authenticate() again
return (request.user, JWTPayload(payload))

# CORRECT — raw Django HttpRequest user (AnonymousUser), no recursion
return (request._request.user, JWTPayload(payload))
```

**Rule:** DRF `authenticate()` must return a real `User` (or `AnonymousUser`) object, **never**
`request.user` (the DRF wrapped property).

---

## 7. `kubectl logs` / `exec` / `port-forward` fail with 502 Bad Gateway

**Symptom:** Any interactive kubectl command against worker node pods returns:
`proxy error from 127.0.0.1:6443 while dialing <worker-ip>:10250, code 502`.

**Cause:** The Kubernetes API server proxies exec/logs/port-forward to the kubelet on port 10250.
The Hetzner firewall blocks this port between the control plane and worker nodes.

**Workaround:** Query **Loki** instead — Promtail runs as a DaemonSet on every node and ships
logs to Loki regardless of the kubelet proxy:
```bash
kubectl -n loki port-forward svc/loki 3100:3100 &
curl -sG "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="no-deposit", container="django"} != "/health/"' \
  --data-urlencode "start=$(date -d '30 minutes ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000" \
  --data-urlencode "limit=100"
```

**Permanent fix:** Add a Hetzner firewall rule allowing TCP 10250 from the control plane node
to worker nodes.

---

## 8. Running `manage.py migrate` when `kubectl exec` is unavailable

**Symptom:** Need to run migrations but `kubectl exec` fails (see issue 7 above).

**Fix:** Run migrations as a one-off Kubernetes pod using `kubectl run` with `--overrides`:
```bash
kubectl -n no-deposit run migrate-job \
  --image=ghcr.io/alexbenisch/no-deposit:latest \
  --restart=Never \
  --image-pull-policy=Always \
  --overrides='{
    "spec": {
      "imagePullSecrets": [{"name": "ghcr-credentials"}],
      "containers": [{
        "name": "migrate-job",
        "image": "ghcr.io/alexbenisch/no-deposit:latest",
        "command": ["python", "manage.py", "migrate"],
        "envFrom": [{"configMapRef": {"name": "no-deposit-django-config"}}],
        "env": [
          {"name": "DJANGO_SECRET_KEY", "valueFrom": {"secretKeyRef": {"name": "no-deposit-django", "key": "DJANGO_SECRET_KEY"}}},
          {"name": "POSTGRES_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "no-deposit-django", "key": "POSTGRES_PASSWORD"}}}
        ]
      }]
    }
  }'
kubectl -n no-deposit wait pod/migrate-job --for=condition=Ready=False --timeout=120s
kubectl -n no-deposit delete pod migrate-job
```
