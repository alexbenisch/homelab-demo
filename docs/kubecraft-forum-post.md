# Deploying Linkding with Flux CD and GitOps - A Learning Journey with Claude Code

## Overview

I recently deployed the Linkding bookmark manager to my K3s cluster using Flux CD and GitOps principles, with assistance from Claude Code. This post documents my journey, the challenges I encountered, and how I solved them. The setup leverages Tailscale for secure networking between my local machine and the control plane.

## Environment Setup

**Infrastructure:**
- K3s cluster (1 control plane + worker nodes)
- Flux CD v2.7.3 for GitOps
- Tailscale network connecting local machine and control plane
- GitHub repository for GitOps manifests

**Network Architecture:**
- Control plane: `100.82.109.98` (on Tailnet)
- Local machine: `100.90.216.62` (on Tailnet)
- Pod network: `10.42.x.x` (Flannel CNI)

## Initial Challenge: Certificate Authority Issues

When I first pushed my code, the K3s server wasn't running correctly due to certificate authority problems. This prevented Flux from properly reconciling the deployment.

## The GitOps Deployment Process

### Repository Structure

```
clusters/staging/
├── flux-system/
│   ├── gotk-components.yaml
│   ├── gotk-sync.yaml
│   └── kustomization.yaml
├── apps.yaml           # Linkding Deployment
├── namespace.yaml      # Linkding Namespace
└── kustomization.yaml  # Main Kustomization
```

## Issues Encountered and Solutions

### Issue 1: Malformed Kustomization File

**Problem:** The first major issue was a malformed `kustomization.yaml` file that had a Namespace resource embedded directly in it:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - namespace.yaml

# This was incorrectly added here!
apiVersion: v1
kind: Namespace
metadata:
  name: linkding
```

**Error from Flux:**
```
kustomize build failed: Failed to read kustomization file under /tmp/kustomization-*/clusters/staging:
kind should be Kustomization or Component
apiVersion for Namespace should be kustomize.config.k8s.io/v1beta1
```

**Root Cause:** A kustomization.yaml file should only contain the Kustomization kind, not actual Kubernetes resources.

**Solution:** Removed the embedded Namespace definition. The Namespace should be in its own file (namespace.yaml) and referenced in the resources list.

### Issue 2: Missing Referenced Files

**Problem:** After fixing the first issue, Flux reported another error:

```
kustomize build failed: accumulating resources: accumulation err='accumulating resources from 'deployment.yaml':
open /tmp/kustomization-*/clusters/staging/deployment.yaml: no such file or directory'
```

**Root Cause:** The kustomization.yaml referenced files that didn't exist:
- Referenced: `deployment.yaml` and `namespace.yaml`
- Actually had: `apps.yaml` only

**Solution:**
1. Created `namespace.yaml` with the Namespace definition
2. Updated kustomization.yaml to reference the correct files:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - apps.yaml
```

3. Added namespace field to the Deployment in apps.yaml:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: linkding
  namespace: linkding  # Added this line
spec:
  replicas: 1
  selector:
    matchLabels:
      app: linkding
  template:
    metadata:
      labels:
        app: linkding
    spec:
      containers:
        - name: linkding
          image: sissbruecker/linkding:1.31.0
          ports:
            - containerPort: 9090
```

## Verification and Testing

### Checking Flux Events

```bash
flux events --all-namespaces
```

This showed the progression from errors to successful reconciliation.

### Verifying the Deployment

```bash
# Check Flux kustomization status
flux get kustomizations

# Verify namespace creation
kubectl get namespaces

# Check deployment status
kubectl get deployments -n linkding

# Verify pod is running
kubectl get pods -n linkding
```

**Result:**
```
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
linkding   1/1     1            1           17s

NAME                        READY   STATUS    RESTARTS   AGE
linkding-55fb4cbfd7-n7bx2   1/1     Running   0          34s
```

### Testing the Application

First, verified the app was responding from inside the pod:

```bash
kubectl exec -n linkding linkding-55fb4cbfd7-n7bx2 -- curl -s -I http://localhost:9090
```

**Response:**
```
HTTP/1.1 302 Found
Location: /bookmarks
```

This confirmed the application was running correctly!

## Accessing the Application Locally

### Understanding kubectl port-forward

Since my local machine and the control plane are both on the same Tailnet, I could use `kubectl port-forward` to access the application locally without needing to SSH into worker nodes.

**How it works:**

```
Browser (localhost:9090)
    ↓
kubectl process (local proxy on 127.0.0.1:9090)
    ↓
Connection: 100.90.216.62:53208 → 100.82.109.98:6443 (API Server on Tailnet)
    ↓
API Server → Pod (10.42.1.5:9090 on wrkr1)
```

**Command:**
```bash
kubectl port-forward -n linkding pod/linkding-55fb4cbfd7-n7bx2 9090:9090
```

**Verification:**
```bash
# Check what's listening on port 9090
ss -tunlp | grep :9090
# Output: kubectl process listening on 127.0.0.1:9090

# Check kubectl's connection to API server
ss -tnp | grep kubectl
# Output: ESTABLISHED connection to 100.82.109.98:6443
```

The application is now accessible at `http://localhost:9090`!

## Key Learnings

1. **Kustomization Files Must Be Clean:** A kustomization.yaml should only contain Kustomization configuration, not actual Kubernetes resources. Resources should be in separate files and referenced via the `resources` list.

2. **File References Must Match Reality:** Ensure all files referenced in kustomization.yaml actually exist in your repository.

3. **Always Add Namespace to Resources:** When deploying to a specific namespace, always include the `namespace` field in your resource metadata.

4. **Flux Events Are Your Friend:** The `flux events` command is invaluable for troubleshooting deployment issues.

5. **kubectl port-forward via Tailnet:** With Tailscale connecting your local machine to the control plane, kubectl port-forward works seamlessly without needing direct access to worker nodes. The kubectl client creates a local proxy that tunnels through the API server to reach pods on any worker node.

6. **GitOps Workflow:** The automated reconciliation by Flux means you just need to:
   - Fix the manifests locally
   - Commit and push to Git
   - Flux automatically detects and applies changes
   - No manual kubectl apply needed!

## Useful Commands Reference

```bash
# Monitor Flux reconciliation
flux get kustomizations
flux events --all-namespaces

# Force reconciliation
flux reconcile kustomization flux-system --with-source

# Check deployment status
kubectl get all -n linkding

# View pod logs
kubectl logs -n linkding <pod-name>

# Test from within pod
kubectl exec -n linkding <pod-name> -- curl http://localhost:9090

# Port forward for local access
kubectl port-forward -n linkding pod/<pod-name> 9090:9090

# Check cluster info
kubectl cluster-info
```

## Conclusion

This experience demonstrated the power of GitOps with Flux CD and how AI assistance (Claude Code) can help troubleshoot and fix issues quickly. The combination of:
- Declarative GitOps manifests
- Automated Flux reconciliation
- Tailscale networking for secure access
- kubectl port-forward for easy local testing

...creates a powerful and developer-friendly workflow for managing Kubernetes applications.

The key is understanding that every layer (kustomization structure, namespace configuration, network access) needs to be properly configured, and tools like `flux events` and `kubectl` commands help you quickly identify and fix issues.

## Resources

- [Flux CD Documentation](https://fluxcd.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Linkding Project](https://github.com/sissbruecker/linkding)
- [Tailscale Kubernetes Guide](https://tailscale.com/kb/1185/kubernetes/)

---

Hope this helps others on their GitOps journey! Feel free to ask questions in the comments.
