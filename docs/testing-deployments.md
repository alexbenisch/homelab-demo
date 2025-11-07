# Testing Kubernetes Deployments

Quick reference guide for testing deployments before setting up ingress.

## Pre-Deployment Checks

### 1. Check Pod Status
```bash
# Get pod details including IP address
kubectl get pod -n <namespace> -o wide

# Check pod logs
kubectl logs -n <namespace> <pod-name>

# Check pod events
kubectl describe pod -n <namespace> <pod-name>
```

## Testing Application Connectivity

### Method 1: Curl Pod IP Directly (Fastest)
```bash
# Get pod IP first
POD_IP=$(kubectl get pod -n <namespace> <pod-name> -o jsonpath='{.status.podIP}')

# Test with temporary curl container
kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
  curl -s -o /dev/null -w "%{http_code}\n" http://$POD_IP:<port>

# Get full headers
kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
  curl -sI http://$POD_IP:<port>
```

### Method 2: Curl from Inside the Pod
```bash
# Test localhost from within the pod
kubectl exec -n <namespace> <pod-name> -- curl -sI http://localhost:<port>
```

### Method 3: Test via Service DNS
```bash
# Format: <service-name>.<namespace>.svc.cluster.local:<port>
kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
  curl -sI http://<service-name>.<namespace>.svc.cluster.local:<port>
```

### Method 4: Port-Forward to Local Machine
```bash
# Forward service port to localhost
kubectl port-forward -n <namespace> svc/<service-name> <local-port>:<service-port>

# Then test from your machine
curl -I http://localhost:<local-port>
```

## Common HTTP Response Codes

- `200 OK` - Application responding normally
- `302 Found` - Redirect (common for login pages or root paths)
- `404 Not Found` - Endpoint doesn't exist (check the path)
- `500 Internal Server Error` - Application error (check logs)
- `Connection refused` - Application not listening on expected port
- `Timeout` - Application not responding (check if pod is ready)

## Example: Testing Linkding Deployment

```bash
# 1. Check pod status
kubectl get pod -n linkding -o wide

# 2. Test pod directly
kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
  curl -sI http://10.42.2.8:9090

# 3. Test via service
kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
  curl -sI http://linkding.linkding.svc.cluster.local:9090

# Expected response:
# HTTP/1.1 302 Found
# Location: /bookmarks
```

## Troubleshooting

### Pod Not Ready
```bash
# Check pod events
kubectl describe pod -n <namespace> <pod-name>

# Check logs
kubectl logs -n <namespace> <pod-name>

# Check previous container logs if pod restarted
kubectl logs -n <namespace> <pod-name> --previous
```

### Connection Issues
```bash
# Verify service exists and has endpoints
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace>

# Check if service selector matches pod labels
kubectl get svc <service-name> -n <namespace> -o yaml
kubectl get pod <pod-name> -n <namespace> --show-labels
```

### DNS Issues
```bash
# Test DNS resolution from a test pod
kubectl run dns-test --image=busybox:1.28 --rm -i --restart=Never -- \
  nslookup <service-name>.<namespace>.svc.cluster.local
```

## Quick Test Script

```bash
#!/bin/bash
NAMESPACE=$1
POD_NAME=$2
PORT=$3

echo "Testing deployment: $POD_NAME in namespace: $NAMESPACE on port: $PORT"
echo "================================================================"

# Get pod status
echo -e "\n1. Pod Status:"
kubectl get pod -n $NAMESPACE $POD_NAME -o wide

# Get pod IP
POD_IP=$(kubectl get pod -n $NAMESPACE $POD_NAME -o jsonpath='{.status.podIP}')
echo -e "\n2. Pod IP: $POD_IP"

# Test pod IP
echo -e "\n3. Testing Pod IP:"
kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
  curl -sI http://$POD_IP:$PORT | head -5

# Test service
SERVICE_NAME=$(kubectl get svc -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}')
echo -e "\n4. Testing Service: $SERVICE_NAME"
kubectl run curl-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
  curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  http://$SERVICE_NAME.$NAMESPACE.svc.cluster.local:$PORT

echo -e "\nTest complete!"
```

Usage:
```bash
chmod +x test-deployment.sh
./test-deployment.sh linkding linkding-55fb4cbfd7-blzgn 9090
```
