# Deploying Tailnet-Only Applications

Guide for deploying applications that are only accessible on your Tailscale network (Tailnet).

## Overview

There are multiple approaches to expose applications exclusively on your Tailnet, each with different trade-offs. This guide covers three main methods.

## Approach Comparison

| Approach | Security | Complexity | Persistence | Best For |
|----------|----------|------------|-------------|----------|
| Tailscale Sidecar | Highest (Zero Trust) | Low | Automatic | k3s, simple setups |
| Tailscale Operator | Highest (Zero Trust) | Medium | Automatic | Multiple services, centralized |
| Ingress + Tailnet IP | Medium | Low | Automatic | Using existing ingress |
| Port Forward | Low | Very Low | Manual | Debugging/admin tools |

---

## Option 1: Tailscale Sidecar Container (Recommended for k3s)

The simplest approach for k3s - add Tailscale as a sidecar container to your deployment. Each pod joins your Tailnet directly.

### How It Works

1. Add Tailscale container to your pod alongside your app
2. Pod joins Tailnet with its own hostname
3. Access via MagicDNS (e.g., `https://myapp.your-tailnet.ts.net`)
4. Automatic HTTPS if MagicDNS is enabled

### Pros

- Simplest setup for k3s
- No operator needed
- Automatic TLS via Tailscale MagicDNS
- Each pod gets its own Tailnet device
- Works with any Kubernetes distribution
- Easy to understand and debug

### Cons

- Sidecar container in each pod (uses more resources)
- Need to add sidecar to each deployment
- Each pod counts as a Tailnet device

### Prerequisites

- Tailscale account with MagicDNS enabled
- Auth key from Tailscale admin console

### Setup Steps

#### 1. Generate Tailscale Auth Key

1. Go to [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
2. Generate a new auth key
3. Settings:
   - **Reusable**: Yes (for multiple services)
   - **Ephemeral**: No (for persistent services)
   - **Tags**: Optional (e.g., `tag:k8s`)

#### 2. Create Encrypted Secret

Create a SOPS-encrypted secret with your auth key:

```yaml
# apps/base/myapp/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tailscale-auth
type: Opaque
stringData:
  TS_AUTHKEY: tskey-auth-xxxxxxxxxxxxx
```

**Encrypt before committing:**
```bash
sops -e -i apps/base/myapp/secret.yaml
```

#### 3. Create Deployment with Sidecar

```yaml
# apps/base/myapp/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      serviceAccountName: myapp

      containers:
        # Your application container
        - name: myapp
          image: myapp/myapp:latest
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: myapp-data
              mountPath: /data

        # Tailscale sidecar container
        - name: tailscale
          image: tailscale/tailscale:latest
          env:
            - name: TS_AUTHKEY
              valueFrom:
                secretKeyRef:
                  name: tailscale-auth
                  key: TS_AUTHKEY
            - name: TS_USERSPACE
              value: "true"
            - name: TS_STATE_DIR
              value: /var/lib/tailscale
            - name: TS_HOSTNAME
              value: "myapp"
            - name: TS_SERVE_CONFIG
              value: /config/serve.json
          volumeMounts:
            - name: tailscale-state
              mountPath: /var/lib/tailscale
            - name: tailscale-config
              mountPath: /config
          securityContext:
            runAsUser: 1000
            runAsGroup: 1000

      volumes:
        - name: myapp-data
          persistentVolumeClaim:
            claimName: myapp-data-pvc
        - name: tailscale-state
          emptyDir: {}
        - name: tailscale-config
          configMap:
            name: tailscale-serve-config
```

#### 4. Create Tailscale Serve Configuration

Tailscale serve configuration tells Tailscale how to proxy to your app:

```yaml
# apps/base/myapp/tailscale-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tailscale-serve-config
data:
  serve.json: |
    {
      "TCP": {
        "443": {
          "HTTPS": true
        }
      },
      "Web": {
        "myapp.your-tailnet.ts.net:443": {
          "Handlers": {
            "/": {
              "Proxy": "http://127.0.0.1:8080"
            }
          }
        }
      }
    }
```

**Note**: Replace `myapp.your-tailnet.ts.net` with your actual Tailnet name, and `8080` with your app's port.

#### 5. Create ServiceAccount

```yaml
# apps/base/myapp/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp
```

#### 6. Update Kustomization

```yaml
# apps/base/myapp/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - serviceaccount.yaml
  - deployment.yaml
  - storage.yaml
  - secret.yaml
  - tailscale-config.yaml
```

#### 7. Deploy and Verify

```bash
# Commit and push
git add apps/base/myapp
git commit -m "Add myapp with Tailscale sidecar"
git push

# Reconcile Flux
flux reconcile kustomization apps --with-source

# Check pod status
kubectl get pods -n myapp

# Check Tailscale connection
kubectl logs -n myapp <pod-name> -c tailscale

# Check Tailscale devices and get the actual hostname
tailscale status

# Test connectivity (note: hostname may have suffix like -1)
curl -I https://myapp-1.your-tailnet.ts.net

# Or test via Tailnet IP
curl -I http://<tailnet-ip>:8080
```

**Important**: Tailscale may add a numeric suffix (e.g., `-1`) to your hostname for uniqueness. Check `tailscale status` to see the actual hostname assigned.

### Simplified Version (Without Serve Config)

If you don't need the serve configuration, you can use an even simpler setup:

```yaml
containers:
  - name: myapp
    image: myapp/myapp:latest
    ports:
      - containerPort: 8080

  - name: tailscale
    image: tailscale/tailscale:latest
    env:
      - name: TS_AUTHKEY
        valueFrom:
          secretKeyRef:
            name: tailscale-auth
            key: TS_AUTHKEY
      - name: TS_USERSPACE
        value: "true"
      - name: TS_HOSTNAME
        value: "myapp"
    securityContext:
      runAsUser: 1000
      runAsGroup: 1000
```

Then access via Tailnet IP and port: `http://myapp.your-tailnet:8080`

---

## Option 2: Tailscale Kubernetes Operator

The Tailscale Kubernetes operator automatically exposes services to your Tailnet with proper DNS and TLS.

### How It Works

1. Install Tailscale operator in your cluster
2. Add annotation to your Kubernetes service
3. Operator creates a Tailscale device for that service
4. Service gets hostname on Tailnet (e.g., `myapp.tailnet-name.ts.net`)
5. Access from any device on your Tailnet

### Pros

- True zero-trust Tailnet-only access
- Automatic TLS via Tailscale
- Proper DNS names (MagicDNS)
- Each service gets its own Tailscale device
- No ingress configuration needed
- Can share with other Tailnet members via ACLs

### Cons

- Requires Tailscale auth key management
- Each exposed service counts as a device in Tailscale
- Additional operator to manage
- More complex initial setup

### Prerequisites

- Tailscale account
- Auth key from Tailscale admin console

### Setup Steps

#### 1. Generate Tailscale Auth Key

1. Go to [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
2. Generate a new auth key
3. Settings:
   - **Reusable**: Yes (for multiple services)
   - **Ephemeral**: No (for persistent services)
   - **Tags**: Optional (e.g., `tag:k8s`)

#### 2. Create Tailscale Secret

Create a sealed secret or SOPS-encrypted secret:

```yaml
# infrastructure/tailscale/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tailscale-auth
  namespace: tailscale
type: Opaque
stringData:
  TS_AUTHKEY: tskey-auth-xxxxxxxxxxxxx
```

**Important**: Encrypt this secret with SOPS before committing:

```bash
sops -e -i infrastructure/tailscale/secret.yaml
```

#### 3. Deploy Tailscale Operator via Flux

Create operator deployment:

```yaml
# infrastructure/tailscale/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tailscale
```

```yaml
# infrastructure/tailscale/operator.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tailscale-operator
  namespace: tailscale
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tailscale-operator
rules:
  - apiGroups: [""]
    resources: ["services", "secrets", "configmaps"]
    verbs: ["*"]
  - apiGroups: ["apps"]
    resources: ["statefulsets", "deployments"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: tailscale-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: tailscale-operator
subjects:
  - kind: ServiceAccount
    name: tailscale-operator
    namespace: tailscale
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tailscale-operator
  namespace: tailscale
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tailscale-operator
  template:
    metadata:
      labels:
        app: tailscale-operator
    spec:
      serviceAccountName: tailscale-operator
      containers:
        - name: operator
          image: tailscale/k8s-operator:latest
          env:
            - name: OPERATOR_NAMESPACE
              value: tailscale
            - name: TS_AUTHKEY
              valueFrom:
                secretKeyRef:
                  name: tailscale-auth
                  key: TS_AUTHKEY
```

```yaml
# infrastructure/tailscale/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - operator.yaml
  - secret.yaml
```

#### 4. Add to Infrastructure Kustomization

```yaml
# infrastructure/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  # ... other resources ...
  - tailscale/
```

#### 5. Expose a Service on Tailnet

Add annotation to your service:

```yaml
# apps/base/myapp/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  annotations:
    tailscale.com/expose: "true"
    # Optional: set custom hostname
    tailscale.com/hostname: "myapp"
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
```

#### 6. Deploy and Verify

```bash
# Commit and push
git add infrastructure/tailscale apps/base/myapp
git commit -m "Add Tailscale operator and expose myapp"
git push

# Reconcile Flux
flux reconcile kustomization infrastructure --with-source
flux reconcile kustomization apps --with-source

# Check operator status
kubectl get pods -n tailscale

# Check Tailscale devices
tailscale status

# Access your app
curl https://myapp.your-tailnet.ts.net
```

### Advanced Configuration

#### Set Custom Hostname

```yaml
annotations:
  tailscale.com/expose: "true"
  tailscale.com/hostname: "custom-name"
```

#### Use Tags for ACL Management

```yaml
annotations:
  tailscale.com/expose: "true"
  tailscale.com/tags: "tag:k8s,tag:internal"
```

#### Expose on Specific Port

```yaml
annotations:
  tailscale.com/expose: "true"
  tailscale.com/tailnet-target-port: "8080"
```

---

## Option 2: Use Existing Ingress with Tailnet IP

Access apps through your existing Traefik ingress using the Tailnet IP of your control plane.

### How It Works

1. Create normal Kubernetes ingress
2. Access via Tailnet IP of control plane
3. Use Host header or local DNS resolution

### Pros

- No additional components needed
- Uses existing ingress infrastructure
- Simple configuration
- Quick to set up

### Cons

- Not truly Tailnet-only (accessible within cluster network)
- Need to manage DNS or use IP directly
- No automatic TLS for Tailnet access
- Still requires ingress controller

### Setup Steps

#### 1. Create Standard Ingress (Without Public TLS)

```yaml
# apps/base/myapp/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    # No cert-manager annotations needed for Tailnet-only
spec:
  rules:
    - host: myapp.internal.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 80
```

#### 2. Find Your Tailnet IP

```bash
# On the control plane
tailscale ip -4
# Example output: 100.64.1.2
```

#### 3. Access Methods

**Method A: Using /etc/hosts**

On your local machine:
```bash
# Add to /etc/hosts
echo "100.64.1.2 myapp.internal.local" | sudo tee -a /etc/hosts
```

Access: `http://myapp.internal.local`

**Method B: Using curl with Host header**

```bash
curl -H "Host: myapp.internal.local" http://100.64.1.2
```

**Method C: Using Tailscale MagicDNS**

1. Enable MagicDNS in Tailscale admin
2. Set up DNS records pointing to control plane IP
3. Access via custom domain

---

## Option 3: Headless Service + Port Forward

Simple port-forwarding for temporary or admin access.

### How It Works

1. Create ClusterIP service (no ingress)
2. Use `kubectl port-forward` over Tailnet connection
3. Access on localhost

### Pros

- Simplest approach
- No extra configuration
- Good for debugging/admin tools
- Truly private (only you can access)

### Cons

- Requires manual port-forward command
- Not persistent (stops when command ends)
- Only accessible from machine running port-forward
- Not suitable for shared access

### Setup Steps

#### 1. Create Service (No Ingress)

```yaml
# apps/base/myapp/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  type: ClusterIP  # Default, no external access
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
```

#### 2. Port Forward

```bash
# Forward to localhost
kubectl port-forward -n myapp svc/myapp 8080:80

# Access at http://localhost:8080
```

#### 3. Make Persistent (Optional)

Create a systemd service or use tmux/screen:

```bash
# Using tmux
tmux new -s myapp-forward
kubectl port-forward -n myapp svc/myapp 8080:80
# Detach: Ctrl+b, d
# Reattach: tmux attach -t myapp-forward
```

---

## Use Case Recommendations

### Use Tailscale Operator When:

- Deploying internal tools (admin panels, monitoring)
- Need to share with team members on Tailnet
- Want proper DNS names and TLS
- Security is critical (zero trust)
- Apps should be permanently accessible

**Examples**:
- Internal wikis
- Admin dashboards
- Development tools
- Private APIs
- Home automation interfaces

### Use Ingress + Tailnet IP When:

- Already have ingress configured
- Quick temporary access needed
- Don't want to manage additional operator
- App might become public later

**Examples**:
- Testing apps before public release
- Internal staging environments
- Apps with mixed public/private access

### Use Port Forward When:

- Debugging applications
- One-time admin tasks
- Database clients
- Very sensitive operations
- Personal use only

**Examples**:
- PostgreSQL admin
- Redis CLI access
- Kubernetes dashboard
- Debug/troubleshooting

---

## Security Best Practices

### For All Approaches

1. **Use Tailscale ACLs** - Restrict access to specific users/devices
2. **Enable MFA** - Protect Tailscale account
3. **Regular key rotation** - Rotate auth keys periodically
4. **Monitor access** - Check Tailscale audit logs
5. **Principle of least privilege** - Only expose what's necessary

### Tailscale ACL Example

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["tag:k8s:*"]
    },
    {
      "action": "accept",
      "src": ["user@example.com"],
      "dst": ["tag:k8s-dev:*"]
    }
  ],
  "tagOwners": {
    "tag:k8s": ["group:admins"],
    "tag:k8s-dev": ["group:developers"]
  }
}
```

---

## Troubleshooting

### Hostname Has Unexpected Suffix (e.g., -1, -2)

Tailscale automatically adds numeric suffixes to ensure hostname uniqueness across your Tailnet.

**To find your actual hostname:**
```bash
# From within the pod
kubectl exec -n <namespace> <pod-name> -c tailscale -- tailscale --socket=/tmp/tailscaled.sock status

# From any Tailnet device
tailscale status
```

**Fix the serve configuration:**
1. Update `tailscale-config.yaml` with the actual hostname (e.g., `myapp-1.your-tailnet.ts.net`)
2. Commit and push changes
3. Reconcile Flux

**Alternative**: Access via Tailnet IP directly (no serve config needed):
```bash
curl http://<tailnet-ip>:<app-port>
```

### HTTPS Not Working / Certificate Errors

**Common causes:**
- Serve config has wrong hostname (see above)
- MagicDNS not enabled in Tailscale admin console
- Serve config not properly loaded

**Verify serve config is loaded:**
```bash
kubectl logs -n <namespace> <pod-name> -c tailscale | grep "serve proxy"

# Should see:
# serve proxy: applying serve config
# serve: creating a new proxy handler for http://127.0.0.1:<port>
```

**Test both HTTPS and HTTP:**
```bash
# HTTPS via MagicDNS
curl -I https://myapp-1.your-tailnet.ts.net

# HTTP via IP
curl -I http://<tailnet-ip>
```

### Tailscale Sidecar Crashes

**Check for RBAC issues:**
```bash
kubectl logs -n <namespace> <pod-name> -c tailscale

# Look for errors like:
# error setting up for running on Kubernetes: some Kubernetes permissions are missing
```

**Solution**: Ensure you have created the RBAC Role and RoleBinding:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: myapp-tailscale
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "create", "update"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["get", "create", "patch"]
```

### Tailscale Operator Not Working

**Check operator logs:**
```bash
kubectl logs -n tailscale -l app=tailscale-operator
```

**Verify auth key:**
```bash
kubectl get secret -n tailscale tailscale-auth -o yaml
```

**Check service annotation:**
```bash
kubectl get svc -n <namespace> <service-name> -o yaml | grep tailscale
```

### Can't Access via Tailnet IP

**Verify Tailnet IP:**
```bash
tailscale status
```

**Check ingress controller:**
```bash
kubectl get pods -n kube-system -l app=traefik
```

**Test directly to pod:**
```bash
kubectl port-forward -n <namespace> <pod-name> 8080:80
```

### Port Forward Connection Drops

**Use longer timeout:**
```bash
kubectl port-forward --pod-running-timeout=24h -n <namespace> svc/<service> 8080:80
```

**Check network stability:**
```bash
ping <tailnet-ip>
```

---

## Complete Example: Private Wiki

Deploy a private wiki only accessible on Tailnet using the operator:

### Directory Structure
```
apps/base/wiki/
├── namespace.yaml
├── deployment.yaml
├── service.yaml
├── storage.yaml
└── kustomization.yaml
```

### service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: wiki
  annotations:
    tailscale.com/expose: "true"
    tailscale.com/hostname: "wiki"
    tailscale.com/tags: "tag:internal"
spec:
  selector:
    app: wiki
  ports:
    - port: 80
      targetPort: 8080
```

### Deploy
```bash
git add apps/base/wiki
git commit -m "Add private wiki on Tailnet"
git push

flux reconcile kustomization apps --with-source

# Access after deployment
curl https://wiki.your-tailnet.ts.net
```

---

## Comparison with Public Apps

| Aspect | Public App | Tailnet-Only App |
|--------|-----------|------------------|
| Ingress | Required with TLS | Optional |
| DNS | Public domain | Tailnet hostname or IP |
| TLS | Let's Encrypt | Tailscale automatic or none |
| Access | Internet | Tailnet members only |
| Security | Firewall + auth | Zero trust network |
| Cost | Domain name | Free with Tailscale |

---

## Migration Path

### From Public to Tailnet-Only

1. Deploy with Tailscale operator
2. Test access via Tailnet
3. Remove public ingress
4. Update DNS/bookmarks

### From Tailnet-Only to Public

1. Create ingress with cert-manager
2. Configure public DNS
3. Test public access
4. Remove Tailscale annotation (optional)
5. Can keep both for hybrid access

---

## Additional Resources

- [Tailscale Kubernetes Operator Docs](https://tailscale.com/kb/1236/kubernetes-operator/)
- [Tailscale ACL Documentation](https://tailscale.com/kb/1018/acls/)
- [MagicDNS Setup Guide](https://tailscale.com/kb/1081/magicdns/)
