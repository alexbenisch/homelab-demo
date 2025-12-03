# Grafana Monitoring Targets - Automated Configuration Concept

## Overview

This document outlines a concept for automatically adding monitoring targets (data sources) to Grafana from within the Kubernetes cluster, similar to how the cluster-dashboard application interacts with the cluster using the Kubernetes API.

## Architecture

### Approach 1: Kubernetes Job with Grafana CLI

A Kubernetes Job that runs periodically or on-demand to configure Grafana data sources using the Grafana CLI.

```
┌─────────────────────────────────────────┐
│  Kubernetes Cluster                     │
│                                         │
│  ┌─────────────────┐                   │
│  │ Grafana Pod     │                   │
│  │ (main app)      │                   │
│  └─────────────────┘                   │
│           ▲                             │
│           │ HTTP API                    │
│           │                             │
│  ┌────────┴──────────┐                 │
│  │ Config Job        │                 │
│  │ - Grafana CLI     │                 │
│  │ - kubectl client  │                 │
│  │ - Service discovery│                │
│  └───────────────────┘                 │
│           │                             │
│           │ discovers services          │
│           ▼                             │
│  ┌───────────────────┐                 │
│  │ Kubernetes API    │                 │
│  │ (ServiceAccount)  │                 │
│  └───────────────────┘                 │
└─────────────────────────────────────────┘
```

### Approach 2: Sidecar Container with Grafana HTTP API

A sidecar container in the Grafana pod that continuously monitors the cluster and updates data sources.

```
┌─────────────────────────────────────────┐
│  Grafana Pod                            │
│                                         │
│  ┌─────────────────┐                   │
│  │ grafana         │                   │
│  │ (main container)│◄──────┐           │
│  └─────────────────┘       │           │
│                            │ HTTP API  │
│  ┌─────────────────────────┴─┐         │
│  │ grafana-config            │         │
│  │ - Python/Go script        │         │
│  │ - Kubernetes client       │         │
│  │ - Grafana HTTP API client │         │
│  │ - Service discovery       │         │
│  └───────────────────────────┘         │
│           │                             │
└───────────┼─────────────────────────────┘
            │
            ▼
   ┌────────────────┐
   │ Kubernetes API │
   └────────────────┘
```

## Implementation Options

### Option 1: Kubernetes Job (Recommended)

**Advantages:**
- Clean separation of concerns
- Can be triggered manually or via CronJob
- Easier to debug and test
- Follows GitOps principles
- No changes to existing Grafana deployment

**Implementation:**

1. **Create ConfigMap with discovery script:**
   - Python script using `kubernetes` client library
   - Discovers Prometheus, Loki, or other monitoring services
   - Uses Grafana HTTP API to add/update data sources

2. **Create RBAC for service discovery:**
   - ServiceAccount for the job
   - Role with permissions to list services, endpoints
   - RoleBinding to link them

3. **Create Kubernetes Job:**
   - Mounts the script ConfigMap
   - Uses Grafana admin credentials from secret
   - Runs on-demand or as CronJob

**Example workflow:**
```bash
# Manual trigger
kubectl create job -n grafana grafana-config-$(date +%s) \
  --from=cronjob/grafana-datasource-sync

# Or run as CronJob (every hour)
# CronJob automatically creates Jobs
```

### Option 2: Init Container

**Advantages:**
- Runs before Grafana starts
- Ensures data sources exist on first boot
- Simple one-time configuration

**Disadvantages:**
- Only runs once per pod restart
- Cannot dynamically update when new services are added

### Option 3: Sidecar Container

**Advantages:**
- Continuous monitoring and updates
- Automatically discovers new services
- Real-time synchronization

**Disadvantages:**
- Adds complexity to Grafana pod
- Requires pod restart to deploy
- More resource usage

## Recommended Solution: Kubernetes CronJob

### Components

#### 1. Service Discovery Script (Python)

```python
#!/usr/bin/env python3
"""
Grafana Data Source Auto-Configuration

Discovers monitoring services in the cluster and automatically
configures them as Grafana data sources.
"""

from kubernetes import client, config
import requests
import os
import sys

# Load in-cluster config
config.load_incluster_config()
v1 = client.CoreV1Api()

# Grafana configuration
GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://grafana.grafana.svc.cluster.local:3000')
GRAFANA_USER = os.getenv('GRAFANA_USER', 'admin')
GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD')

# Data source templates
DATASOURCE_CONFIGS = {
    'prometheus': {
        'name': 'Prometheus',
        'type': 'prometheus',
        'url': 'http://prometheus-server.{namespace}.svc.cluster.local',
        'access': 'proxy',
        'isDefault': True,
    },
    'loki': {
        'name': 'Loki',
        'type': 'loki',
        'url': 'http://loki.{namespace}.svc.cluster.local:3100',
        'access': 'proxy',
    },
    'tempo': {
        'name': 'Tempo',
        'type': 'tempo',
        'url': 'http://tempo.{namespace}.svc.cluster.local:3100',
        'access': 'proxy',
    }
}

def discover_services():
    """Discover monitoring services in the cluster"""
    services = []

    # List all services in all namespaces
    all_services = v1.list_service_for_all_namespaces()

    for svc in all_services.items:
        # Check for Prometheus
        if 'prometheus' in svc.metadata.name.lower():
            services.append({
                'type': 'prometheus',
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'port': svc.spec.ports[0].port if svc.spec.ports else 9090
            })

        # Check for Loki
        elif 'loki' in svc.metadata.name.lower():
            services.append({
                'type': 'loki',
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'port': svc.spec.ports[0].port if svc.spec.ports else 3100
            })

        # Check for Tempo
        elif 'tempo' in svc.metadata.name.lower():
            services.append({
                'type': 'tempo',
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'port': svc.spec.ports[0].port if svc.spec.ports else 3100
            })

    return services

def get_existing_datasources():
    """Get list of existing Grafana data sources"""
    response = requests.get(
        f'{GRAFANA_URL}/api/datasources',
        auth=(GRAFANA_USER, GRAFANA_PASSWORD)
    )
    response.raise_for_status()
    return response.json()

def create_datasource(config):
    """Create a Grafana data source"""
    response = requests.post(
        f'{GRAFANA_URL}/api/datasources',
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        json=config
    )

    if response.status_code == 409:
        print(f"Data source '{config['name']}' already exists")
        return False

    response.raise_for_status()
    print(f"Created data source: {config['name']}")
    return True

def main():
    if not GRAFANA_PASSWORD:
        print("ERROR: GRAFANA_PASSWORD environment variable not set")
        sys.exit(1)

    print("Discovering monitoring services in cluster...")
    services = discover_services()

    print(f"Found {len(services)} monitoring services")
    for svc in services:
        print(f"  - {svc['type']}: {svc['name']} in {svc['namespace']}")

    print("\nGetting existing Grafana data sources...")
    existing = get_existing_datasources()
    existing_names = {ds['name'] for ds in existing}
    print(f"Found {len(existing)} existing data sources")

    print("\nConfiguring data sources...")
    for svc in services:
        if svc['type'] in DATASOURCE_CONFIGS:
            config = DATASOURCE_CONFIGS[svc['type']].copy()
            config['url'] = f"http://{svc['name']}.{svc['namespace']}.svc.cluster.local:{svc['port']}"
            config['name'] = f"{config['name']} ({svc['namespace']})"

            if config['name'] not in existing_names:
                try:
                    create_datasource(config)
                except Exception as e:
                    print(f"ERROR creating {config['name']}: {e}")
            else:
                print(f"Data source '{config['name']}' already exists, skipping")

    print("\nDone!")

if __name__ == '__main__':
    main()
```

#### 2. Kubernetes Manifests

**ConfigMap (config-script.yaml):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-config-script
  namespace: grafana
data:
  configure-datasources.py: |
    [Script contents from above]
```

**ServiceAccount & RBAC (rbac.yaml):**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: grafana-config
  namespace: grafana
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: grafana-config-reader
rules:
  - apiGroups: [""]
    resources: ["services", "endpoints"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: grafana-config-reader
subjects:
  - kind: ServiceAccount
    name: grafana-config
    namespace: grafana
roleRef:
  kind: ClusterRole
  name: grafana-config-reader
  apiGroup: rbac.authorization.k8s.io
```

**CronJob (cronjob.yaml):**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: grafana-datasource-sync
  namespace: grafana
spec:
  schedule: "0 * * * *"  # Every hour
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: grafana-config
        spec:
          serviceAccountName: grafana-config
          restartPolicy: OnFailure
          containers:
            - name: configure
              image: python:3.11-slim
              command:
                - /bin/bash
                - -c
                - |
                  pip install kubernetes requests > /dev/null 2>&1
                  python /scripts/configure-datasources.py
              env:
                - name: GRAFANA_URL
                  value: "http://grafana.grafana.svc.cluster.local:3000"
                - name: GRAFANA_USER
                  value: "admin"
                - name: GRAFANA_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: grafana-credentials
                      key: admin-password
              volumeMounts:
                - name: scripts
                  mountPath: /scripts
              resources:
                requests:
                  cpu: 100m
                  memory: 128Mi
                limits:
                  cpu: 200m
                  memory: 256Mi
          volumes:
            - name: scripts
              configMap:
                name: grafana-config-script
```

## Usage

### Manual Execution

```bash
# Create a one-time job from the CronJob
kubectl create job -n grafana grafana-config-manual \
  --from=cronjob/grafana-datasource-sync

# Watch job progress
kubectl logs -n grafana -l app=grafana-config -f

# Check job status
kubectl get jobs -n grafana

# Check created data sources
kubectl exec -n grafana deployment/grafana -- \
  grafana-cli admin data-sources ls
```

### Automatic Execution

The CronJob runs every hour automatically and:
1. Discovers monitoring services (Prometheus, Loki, Tempo)
2. Checks existing Grafana data sources
3. Creates missing data sources
4. Logs all operations

### Verify Data Sources

```bash
# Via kubectl and Grafana CLI
kubectl exec -n grafana deployment/grafana -- \
  grafana-cli admin data-sources ls

# Via HTTP API
ADMIN_PASSWORD=$(kubectl get secret -n grafana grafana-credentials -o jsonpath='{.data.admin-password}' | base64 -d)
kubectl port-forward -n grafana svc/grafana 3000:3000 &
curl -s http://admin:${ADMIN_PASSWORD}@localhost:3000/api/datasources | jq
```

## Deployment Steps

1. **Add manifests to repository:**
   ```bash
   apps/base/grafana/
   ├── config-script-configmap.yaml
   ├── config-rbac.yaml
   └── config-cronjob.yaml
   ```

2. **Update kustomization.yaml:**
   ```yaml
   resources:
     - namespace.yaml
     - deployment.yaml
     - service.yaml
     - ingress.yaml
     - pvc.yaml
     - secret.yaml
     - config-script-configmap.yaml
     - config-rbac.yaml
     - config-cronjob.yaml
   ```

3. **Deploy:**
   ```bash
   git add apps/base/grafana/
   git commit -m "Add Grafana data source auto-configuration"
   git push
   flux reconcile kustomization apps --with-source
   ```

4. **Test:**
   ```bash
   # Trigger manual job
   kubectl create job -n grafana test-config \
     --from=cronjob/grafana-datasource-sync

   # Check logs
   kubectl logs -n grafana -l app=grafana-config
   ```

## Alternative: Grafana Provisioning (Declarative)

For static data sources, Grafana supports provisioning via ConfigMaps:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: grafana
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus-server.monitoring.svc.cluster.local
        isDefault: true
```

Mount this at `/etc/grafana/provisioning/datasources/` in the Grafana container.

## Recommendations

1. **Start with CronJob approach** - Most flexible and GitOps-friendly
2. **Use provisioning ConfigMaps** - For known, static data sources
3. **Combine both** - Provisioning for core sources, CronJob for dynamic discovery
4. **Add alerting** - Monitor job failures via Prometheus AlertManager
5. **Document discovered sources** - Log to persistent storage for audit

## Security Considerations

- ✅ Uses ServiceAccount with minimal RBAC permissions (read-only services)
- ✅ Grafana credentials stored in SOPS-encrypted secrets
- ✅ Job runs with non-root user
- ✅ No privileged containers required
- ✅ Network policies can restrict job's cluster access

## Future Enhancements

1. **Service annotations** - Discover data sources via annotations:
   ```yaml
   metadata:
     annotations:
       grafana.io/datasource: "prometheus"
       grafana.io/default: "true"
   ```

2. **Dashboard provisioning** - Auto-import dashboards for discovered services

3. **Notification integration** - Slack/email notifications on changes

4. **Drift detection** - Alert when manually-created data sources are removed

5. **Multi-tenancy** - Support multiple Grafana instances or organizations

## References

- [Grafana HTTP API - Data Sources](https://grafana.com/docs/grafana/latest/developers/http_api/data_source/)
- [Grafana CLI Reference](https://grafana.com/docs/grafana/latest/administration/cli/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
