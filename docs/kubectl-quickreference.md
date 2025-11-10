# Set the context to "default" (your k3s cluster)
  kubectl config use-context default

  Your kubectl is now configured to use:
  - Cluster: Your k3s homelab cluster at xxx.xxx.xxx.xxx:6443 (via Tailscale)
  - Nodes: ctrl, wrkr1, wrkr2
  - Config file: /home/alex/.kube/config (the default location)

  Quick Reference

  To switch between contexts in the future:
  # List all available contexts
  kubectl config get-contexts

  # Switch to your k3s cluster
  kubectl config use-context default

  # Switch to GKE cluster (when it exists)
  kubectl config use-context gke_learning-cluster

  # See current context
  kubectl config current-context

