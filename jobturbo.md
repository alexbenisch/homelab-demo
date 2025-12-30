Gut. **Ein Kubernetes-Deployment mit App + Datenbank** ist für dein `homelab-demo` **genau die richtige Flughöhe**. Jetzt gehen wir strukturiert vor – so, dass es **realistisch**, **vorzeigbar** und **erweiterbar** ist.

Ich schlage vor: **Freelance-Radar als Kubernetes-Workload mit PostgreSQL**.

---

## 🎯 Zielbild (klar & ehrlich)

* Läuft **lokal im Homelab** (k3s / kind / microk8s)
* 1 Python/FastAPI-App
* 1 PostgreSQL-Datenbank
* Konfiguration via ConfigMaps + Secrets
* Keine Magie, kein Helm-Overkill (noch nicht)

---

## 📁 Repo-Struktur (`homelab-demo`)

```text
homelab-demo/
├── apps/
│   └── freelance-radar/
│       ├── app/
│       │   ├── main.py
│       │   └── requirements.txt
│       ├── Dockerfile
│       └── README.md
├── k8s/
│   └── freelance-radar/
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── postgres/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── pvc.yaml
│       ├── app/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       └── ingress.yaml
└── README.md
```

👉 **Trennung App / Kubernetes** ist wichtig. Kunden achten darauf.

---

## 🧱 Komponenten im Detail

### 1️⃣ Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: freelance-radar
```

---

### 2️⃣ PostgreSQL (Stateful, aber simpel)

**PVC**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: freelance-radar
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 5Gi
```

**Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: freelance-radar
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          envFrom:
            - secretRef:
                name: postgres-secret
          ports:
            - containerPort: 5432
          volumeMounts:
            - mountPath: /var/lib/postgresql/data
              name: data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: postgres-data
```

**Service**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: freelance-radar
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
```

---

### 3️⃣ App (FastAPI)

**Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: freelance-radar
  namespace: freelance-radar
spec:
  replicas: 1
  selector:
    matchLabels:
      app: freelance-radar
  template:
    metadata:
      labels:
        app: freelance-radar
    spec:
      containers:
        - name: app
          image: freelance-radar:latest
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef:
                name: app-config
          ports:
            - containerPort: 8000
```

**Service**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: freelance-radar
  namespace: freelance-radar
spec:
  selector:
    app: freelance-radar
  ports:
    - port: 80
      targetPort: 8000
```

---

### 4️⃣ Config & Secrets

**ConfigMap**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: freelance-radar
data:
  DATABASE_HOST: postgres
  DATABASE_NAME: radar
```

**Secret**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: freelance-radar
type: Opaque
stringData:
  POSTGRES_USER: radar
  POSTGRES_PASSWORD: radar123
  POSTGRES_DB: radar
```

👉 Ja, **Plaintext ist für Demo ok**. Später: SOPS/Vault.

---

## 🐍 Minimal-App (FastAPI)

```python
from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db")
def db():
    conn = psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        dbname=os.getenv("DATABASE_NAME"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    return {"db": cur.fetchone()[0]}
```

---

## 🚀 Lokales Deployment (Homelab)

```bash
kubectl apply -f k8s/freelance-radar/namespace.yaml
kubectl apply -f k8s/freelance-radar/postgres/
kubectl apply -f k8s/freelance-radar/
```

Bei k3s/kind:

```bash
kubectl port-forward svc/freelance-radar 8080:80 -n freelance-radar
```

---

## 💡 Warum das überzeugt

* **Stateful + Stateless sauber getrennt**
* Kubernetes-Basics sitzen
* Kein Spielzeug-Demo
* Exakt das, was Kunden im Alltag brauchen

---

## 🔜 Sinnvolle nächste Schritte (ich empfehle diese Reihenfolge)

1. Init-Job für DB-Schema (K8s Job)
2. Readiness/Liveness Probes
3. Helm-Chart **oder** Kustomize
4. GitHub Actions: build → load into k3s
5. Optional: Ingress + TLS

Wenn du willst, mache ich als Nächstes:
👉 **ein vollständiges erstes Commit (Dateinamen + Inhalte)**
oder
👉 **Helm-Chart aus genau dieser Struktur**

Sag mir, **was davon als Nächstes rein soll**.

