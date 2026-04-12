# Debugging Ruleset — No-Deposit Homelab

Structured workflow for diagnosing bugs. Follow this exactly before speculating or making
code changes. Each step costs fewer tokens than one wrong guess.

---

## Rule 0 — Stop. Get the error first.

Never change code based on a symptom description alone. The actual traceback always contains
the root cause. Everything else is guessing.

**Do not proceed to any other step until you have the full error message and traceback.**

---

## Step 1 — Establish the error

### 1a. What is the HTTP status?
- **400** → request is malformed or `ALLOWED_HOSTS` rejection
- **401/403** → authentication or permission failure
- **404** → URL not registered or object not found
- **500** → unhandled Python exception → **must get traceback**
- **502/503** → upstream service down or misconfigured

### 1b. Is it reproducible?
Reproduce the error before investigating. Don't debug a ghost. State the exact URL and action.

---

## Step 2 — Get logs (always Loki, never guess)

`kubectl logs` and `kubectl exec` are broken on this cluster for wrkr1 pods (kubelet port
10250 blocked by Hetzner firewall). **Use Loki.**

```bash
# Start Loki tunnel
kubectl -n loki port-forward svc/loki 3100:3100 &

# Get all non-health logs for a container in the last N minutes
START=$(date -d '10 minutes ago' +%s)000000000
END=$(date +%s)000000000
curl -sG "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="no-deposit", container="django"} != "/health/"' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode "limit=100" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('data',{}).get('result',[]):
    for ts, line in sorted(r.get('values',[]), key=lambda x: x[0]):
        try:
            obj = json.loads(line)
            print(obj.get('exc_info') or obj.get('message',''))
        except:
            print(line[:600])
"
```

### Container names by deployment
| Deployment | Container label |
|---|---|
| `no-deposit-django` | `django` |
| `no-deposit-celery-worker` | `celery-worker` |
| `no-deposit-oauth2-proxy` | `oauth2-proxy` |

### For 500 errors — get the full traceback
```bash
curl -sG "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="no-deposit", container="django"} |= "Internal Server Error"' \
  --data-urlencode "start=$START" --data-urlencode "end=$END" --data-urlencode "limit=5" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('data',{}).get('result',[]):
    for _, line in r.get('values',[]):
        try: print(json.loads(line).get('exc_info',''))
        except: print(line)
"
```

---

## Step 3 — Read the traceback bottom-up

The root cause is at the **bottom** of the traceback (the last `File` + exception line).
The call stack above is context — read it only if the final line doesn't make sense alone.

```
Traceback (most recent call last):          ← top: entry point
  File "django/core/handlers/base.py" ...
  File "rest_framework/views.py" ...
  File "app/core/auth.py", line 66          ← your code: THIS is where to look
    return (request.user, JWTPayload(...))
  File "rest_framework/request.py", line 232 ← calls back into auth → infinite loop
RecursionError: maximum recursion depth      ← root cause: THIS is the fix target
```

---

## Step 4 — Identify the fix category

| Bottom-of-traceback pattern | Fix category |
|---|---|
| `RecursionError` | Circular call — find the cycle |
| `AttributeError: 'NoneType'` | Null check missing — find where None enters |
| `DoesNotExist` | DB query — check migrations ran, data exists |
| `ImproperlyConfigured` | Missing setting — check env var / ConfigMap |
| `OperationalError` (psycopg2) | DB connection — check Postgres pod + secret |
| `ImportError` / `ModuleNotFoundError` | Missing dependency — check pyproject.toml |
| `PermissionDenied` / `403` | Role/permission logic — check JWT claims |
| `PyJWKClientConnectionError` | JWKS unreachable — check Keycloak pod + DNS |

---

## Step 5 — Make exactly one change

- Fix the identified root cause only. Don't touch surrounding code.
- Do not add error handling for problems you haven't seen.
- Do not refactor while fixing.

Commit message format: `Fix <what broke>: <one-line root cause>`

---

## Step 6 — Verify the fix

After deploying:
1. Reproduce the original action that caused the error
2. Check Loki: confirm no new 500 for that endpoint
3. Confirm expected HTTP status (200 for success, 401 if unauthenticated, etc.)

If the fix didn't work, **go back to Step 2** — do not make another guess.

---

## Infrastructure quick-checks (run before blaming code)

```bash
# Are pods healthy?
kubectl -n no-deposit get pods

# Did the new image deploy? (check image digest in pod spec)
kubectl -n no-deposit get pod -l app=no-deposit-django -o jsonpath='{.items[0].spec.containers[0].image}'

# Did migrations run?
kubectl -n no-deposit run check-migrations --image=ghcr.io/alexbenisch/no-deposit:latest \
  --restart=Never --image-pull-policy=Always \
  --overrides='{"spec":{"imagePullSecrets":[{"name":"ghcr-credentials"}],"containers":[{"name":"c","image":"ghcr.io/alexbenisch/no-deposit:latest","command":["python","manage.py","showmigrations"],"envFrom":[{"configMapRef":{"name":"no-deposit-django-config"}}],"env":[{"name":"DJANGO_SECRET_KEY","valueFrom":{"secretKeyRef":{"name":"no-deposit-django","key":"DJANGO_SECRET_KEY"}}},{"name":"POSTGRES_PASSWORD","valueFrom":{"secretKeyRef":{"name":"no-deposit-django","key":"POSTGRES_PASSWORD"}}}]}]}}'

# Is the secret present?
kubectl -n no-deposit get secret ghcr-credentials
kubectl -n no-deposit get secret no-deposit-django

# Force Flux to reconcile
flux reconcile kustomization apps --with-source
```

---

## Known cluster constraints

| Issue | Detail |
|---|---|
| `kubectl logs` / `exec` fail on wrkr1 | Port 10250 blocked — use Loki |
| All no-deposit pods land on wrkr1 | No affinity rules set |
| `kubectl port-forward` fails on wrkr1 pods | Same kubelet proxy issue |
| Keycloak direct access grants disabled | Can't get tokens via password grant for testing |
| GHCR image is private | Always need `ghcr-credentials` imagePullSecret |

---

## What NOT to do

- **Do not change code based on the symptom description** — always get the traceback first
- **Do not make multiple changes at once** — you won't know which one fixed it
- **Do not check Loki once and declare "no errors"** — confirm the time range covers the reproduction
- **Do not restart pods to "see if it fixes itself"** — find the cause first
- **Do not add broad exception handlers** to hide errors — fix the root cause
