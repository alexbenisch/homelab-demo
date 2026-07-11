---
title: "Homelab Shutdown — July 2026"
author: "Alex Benisch"
date: 2026-07-11
geometry: "margin=1.5cm"
papersize: a4
---

# Homelab Shutdown — July 2026

Full teardown of the Hetzner-hosted k3s cluster and associated infrastructure.

---

## Infrastructure at shutdown

### Hetzner Cloud compute (`terraform/`)

| Resource | Name | Type | Location |
|---|---|---|---|
| Server — control plane | `ctrl` | `cpx11` | `nbg1` |
| Server — worker 1 | `wrkr1` | `cpx11` | `nbg1` |
| Server — worker 2 | `wrkr2` | `cpx11` | `nbg1` |
| Private network | `homelab-demo-network` | `10.0.0.0/16` | `eu-central` |
| Subnet | — | `10.0.1.0/24` | `eu-central` |
| Firewall | `homelab-demo-firewall` | TCP 22, 80, 443, 6443 | — |
| SSH key | `alex-tpad` | ed25519 | — |

Private IPs: control plane `10.0.1.10`, wrkr1 `10.0.1.20`, wrkr2 `10.0.1.21`.

### Hetzner DNS (`terraform/dns/`)

- Zone: `k8s-demo.de` (primary, TTL 3600)
- Subdomains managed as Terraform variables

### Cloudflare DNS (not in Terraform)

- Zone: `kubetest.uk` — managed at runtime by `external-dns`
  (`apps/base/external-dns/`, `policy: sync`, `txtOwnerId: mercury-cluster`)
- Records were created automatically from Ingress annotations and will be
  absent once the cluster is gone. The zone itself remains in Cloudflare.

### GitOps repo

- `github.com/alexbenisch/homelab-demo` — not destroyed, full history preserved
- GHCR images (`ghcr.io/alexbenisch/*`) — not destroyed

---

## Shutdown procedure

### Prerequisites

- Hetzner Cloud API token (`hcloud_token`)
- Terraform ≥ 1.0 installed locally
- State files must exist locally (not committed — check `terraform/terraform.tfstate`)

### Step 1 — Destroy compute

```bash
cd ~/repos/homelab-demo/terraform
terraform init
terraform destroy -var="hcloud_token=<TOKEN>"
```

Review the plan Terraform prints before typing `yes`. Resources destroyed:
3 servers, network, subnet, firewall, SSH key.

### Step 2 — Destroy Hetzner DNS zone (optional)

Only needed if the `k8s-demo.de` zone is no longer required.

```bash
cd ~/repos/homelab-demo/terraform/dns
terraform init
terraform destroy -var="hcloud_token=<TOKEN>"
```

### Step 3 — Clean up Cloudflare (manual)

External-dns records (`*.kubetest.uk`) will become stale once the cluster
is gone. Either:
- Delete the subdomains in the Cloudflare dashboard, or
- Leave them — they point to IPs that no longer serve traffic

The `kubetest.uk` zone itself should be retained if the domain is still registered.

### Step 4 — Local cleanup

```bash
# Remove kubeconfig entries for the old cluster
kubectl config delete-context homelab   # adjust context name as needed
kubectl config delete-cluster homelab

# Remove SOPS age key if no longer needed (back it up first)
# Located at: ~/.config/sops/age/keys.txt (or wherever configured in .sops.yaml)
```

---

## Rebuilding

To restore the cluster from scratch:

```bash
# 1. Provision servers
cd ~/repos/homelab-demo/terraform
terraform init
terraform apply -var="hcloud_token=<TOKEN>"

# 2. Wait ~3 minutes for cloud-init, then retrieve kubeconfig
scp alex@<ctrl-ip>:/home/alex/.kube/config ~/.kube/config
sed -i 's/127.0.0.1/<ctrl-ip>/g' ~/.kube/config

# 3. Bootstrap Flux
flux bootstrap github \
  --owner=alexbenisch \
  --repository=homelab-demo \
  --branch=main \
  --path=clusters/staging \
  --personal

# 4. Restore SOPS secret so Flux can decrypt sealed secrets
kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey=<path-to-age-key>
```

Full Flux reconcile takes ~10 minutes. External-dns recreates all
`kubetest.uk` DNS records automatically from Ingress annotations.

---

## Notes

- No persistent data was lost: all workloads in this cluster were stateless
  demos or had data backed by Hetzner volumes (none were provisioned).
- Cert-manager TLS certificates will need to be re-issued on rebuild
  (Let's Encrypt will reissue automatically via DNS-01 challenge once
  the Ingresses are live and DNS resolves).
- Kyverno PSS policies added in June 2026 are in Audit mode — no
  workloads were blocked at shutdown.
