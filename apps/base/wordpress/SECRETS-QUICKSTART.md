# WordPress Secrets Quick Start Guide

Quick reference for setting up and managing WordPress secrets with GitHub Actions and SOPS.

## 🚀 Quick Setup (5 minutes)

### Step 1: Add GitHub Secrets

Go to your repository settings and add these 10 secrets:

**Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | Example/Command |
|------------|-------------|-----------------|
| `SOPS_AGE_KEY` | Your SOPS age private key | `cat ~/.config/sops/age/keys.txt` |
| `MYSQL_ROOT_PASSWORD` | MySQL root password | `openssl rand -base64 32` |
| `MYSQL_USER` | MySQL username for WordPress | `wordpress` |
| `MYSQL_PASSWORD` | MySQL user password | `openssl rand -base64 24` |
| `WP_ADMIN_USER` | WordPress admin username | `admin` |
| `WP_ADMIN_PASSWORD` | WordPress admin password | `openssl rand -base64 24` |
| `WP_ADMIN_EMAIL` | WordPress admin email | `admin@k8s-demo.de` |
| `CHATBOT_API_USER` | Chatbot API username | `wordpress` |
| `CHATBOT_API_PASSWORD` | Chatbot API password | `openssl rand -base64 24` |
| `CHATBOT_DEFAULT_LANGUAGE` | Chatbot language | `de` |

### Step 2: Run the Workflow

```bash
# Via GitHub CLI
gh workflow run wordpress-secrets-update.yaml

# Or go to: Actions → Update WordPress Secrets → Run workflow
```

### Step 3: Verify

```bash
# Pull the updated secret file
git pull

# Check it was updated
git log --oneline -n 1 apps/base/wordpress/secret.yaml

# Verify encryption (should see ENC[...] values)
cat apps/base/wordpress/secret.yaml
```

### Step 4: Deploy

The encrypted secret is now in your repo and ready for deployment:

```bash
# Via Flux (if using GitOps)
flux reconcile kustomization apps --with-source

# Or manually
kubectl apply -k apps/base/wordpress/
```

## 📋 Using GitHub CLI (Fastest)

If you have `gh` CLI installed:

```bash
# 1. Set your repository (replace with yours)
REPO="alexbenisch/homelab-demo"

# 2. Add all secrets at once
gh secret set SOPS_AGE_KEY --repo $REPO < ~/.config/sops/age/keys.txt
gh secret set MYSQL_ROOT_PASSWORD --repo $REPO --body "$(openssl rand -base64 32)"
gh secret set MYSQL_USER --repo $REPO --body "wordpress"
gh secret set MYSQL_PASSWORD --repo $REPO --body "$(openssl rand -base64 24)"
gh secret set WP_ADMIN_USER --repo $REPO --body "admin"
gh secret set WP_ADMIN_PASSWORD --repo $REPO --body "$(openssl rand -base64 24)"
gh secret set WP_ADMIN_EMAIL --repo $REPO --body "admin@k8s-demo.de"
gh secret set CHATBOT_API_USER --repo $REPO --body "wordpress"
gh secret set CHATBOT_API_PASSWORD --repo $REPO --body "$(openssl rand -base64 24)"
gh secret set CHATBOT_DEFAULT_LANGUAGE --repo $REPO --body "de"

# 3. Run the workflow
gh workflow run wordpress-secrets-update.yaml

# 4. Monitor the run
gh run list --workflow=wordpress-secrets-update.yaml --limit 1
gh run watch  # Watch the latest run
```

## 🔄 Updating a Secret

To update any secret later:

```bash
# 1. Update the GitHub Secret
gh secret set WP_ADMIN_PASSWORD --body "new-secure-password"

# 2. Re-run the workflow (it will re-encrypt everything)
gh workflow run wordpress-secrets-update.yaml

# 3. Pull and deploy
git pull
kubectl rollout restart deployment/wordpress -n wordpress
```

## 🔍 Viewing Secrets

### View encrypted secret (safe to view)
```bash
cat apps/base/wordpress/secret.yaml
```

### Decrypt secret locally (requires SOPS key)
```bash
sops -d apps/base/wordpress/secret.yaml
```

### Get secret from Kubernetes (if deployed)
```bash
# View all secret keys
kubectl get secret wordpress-secret -n wordpress -o json | jq -r '.data | keys'

# Decode a specific value
kubectl get secret wordpress-secret -n wordpress -o jsonpath='{.data.WP_ADMIN_USER}' | base64 -d

# Get WordPress admin credentials
echo "Username: $(kubectl get secret wordpress-secret -n wordpress -o jsonpath='{.data.WP_ADMIN_USER}' | base64 -d)"
echo "Password: $(kubectl get secret wordpress-secret -n wordpress -o jsonpath='{.data.WP_ADMIN_PASSWORD}' | base64 -d)"
```

## 🎯 Common Tasks

### Generate Strong Passwords
```bash
# 32 characters (for root passwords)
openssl rand -base64 32

# 24 characters (for regular passwords)
openssl rand -base64 24

# Using pwgen
pwgen -s 32 1
```

### Backup Age Key
```bash
# Backup your age key (IMPORTANT!)
cp ~/.config/sops/age/keys.txt ~/age-key-backup-$(date +%Y%m%d).txt

# Store in password manager or secure location
```

### List All GitHub Secrets
```bash
gh secret list
```

### Delete a Secret
```bash
gh secret delete WP_ADMIN_PASSWORD
```

## 🔒 Security Notes

- ✅ GitHub Secrets are encrypted at rest
- ✅ SOPS encrypts secrets before committing to Git
- ✅ Age key is never committed to repository
- ✅ Temporary decrypted files are cleaned up
- ⚠️ Keep your age key secure - without it, you cannot decrypt secrets
- ⚠️ Only repository admins should access GitHub Secrets
- ⚠️ Rotate passwords regularly

## 📚 Full Documentation

For detailed information, see:
- [WORDPRESS-SECRETS-SETUP.md](../../.github/workflows/WORDPRESS-SECRETS-SETUP.md) - Complete setup guide
- [secret.yaml.template](./secret.yaml.template) - Secret structure reference
- [REDEPLOYMENT-STRATEGY.md](./REDEPLOYMENT-STRATEGY.md) - Deployment strategy

## ❓ Troubleshooting

### "SOPS_AGE_KEY not found"
```bash
# Add the age key to GitHub Secrets
gh secret set SOPS_AGE_KEY < ~/.config/sops/age/keys.txt
```

### "failed to decrypt"
```bash
# Verify age key matches
age-keygen -y ~/.config/sops/age/keys.txt
grep "recipient:" apps/base/wordpress/secret.yaml
# Public keys should match
```

### Workflow runs but no changes
- This is normal if secrets haven't changed
- Check GitHub Actions logs for details:
  ```bash
  gh run view --log
  ```

## 🎉 You're Done!

Your WordPress secrets are now:
1. ✅ Stored securely in GitHub Secrets
2. ✅ Encrypted with SOPS in your Git repository
3. ✅ Ready to be deployed to Kubernetes
4. ✅ Manageable through GitHub Actions workflow

Next: Deploy WordPress using the updated secrets!
