# WordPress Secrets Management Setup

This guide explains how to set up and manage WordPress secrets using GitHub Secrets and SOPS encryption.

## Architecture

```
GitHub Secrets (encrypted at rest in GitHub)
    ↓
GitHub Actions Workflow (wordpress-secrets-update.yaml)
    ↓
SOPS Encryption (using age key)
    ↓
Committed to Git (apps/base/wordpress/secret.yaml)
    ↓
Deployed to Kubernetes (by Flux or kubectl)
```

## Required GitHub Secrets

You need to add the following secrets to your GitHub repository:

### 1. SOPS Age Key

**Secret Name:** `SOPS_AGE_KEY`

**How to get it:**
```bash
# If you already have the age key used to encrypt secrets:
cat ~/.config/sops/age/keys.txt

# Or find it in your SOPS configuration
# Copy the entire private key including the header
# It should look like:
# AGE-SECRET-KEY-1...
```

**How to add it:**
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `SOPS_AGE_KEY`
5. Value: Paste your age private key
6. Click "Add secret"

### 2. MySQL Secrets

**Secret Names:**
- `MYSQL_ROOT_PASSWORD` - Root password for MySQL
- `MYSQL_USER` - WordPress MySQL username
- `MYSQL_PASSWORD` - WordPress MySQL password

**Example values:**
```bash
# Generate strong passwords
openssl rand -base64 32  # For MYSQL_ROOT_PASSWORD
openssl rand -base64 24  # For MYSQL_PASSWORD

# Username (simple)
MYSQL_USER=wordpress
```

### 3. WordPress Admin Secrets

**Secret Names:**
- `WP_ADMIN_USER` - WordPress admin username
- `WP_ADMIN_PASSWORD` - WordPress admin password
- `WP_ADMIN_EMAIL` - WordPress admin email

**Example values:**
```bash
# Generate strong password
openssl rand -base64 24  # For WP_ADMIN_PASSWORD

# Other values
WP_ADMIN_USER=admin
WP_ADMIN_EMAIL=admin@k8s-demo.de
```

### 4. Chatbot API Secrets

**Secret Names:**
- `CHATBOT_API_USER` - Chatbot API username
- `CHATBOT_API_PASSWORD` - Chatbot API password
- `CHATBOT_DEFAULT_LANGUAGE` - Default chatbot language

**Example values:**
```bash
# Generate API credentials
openssl rand -base64 24  # For CHATBOT_API_PASSWORD

# Other values
CHATBOT_API_USER=wordpress
CHATBOT_DEFAULT_LANGUAGE=de
```

## Adding Secrets to GitHub

### Via Web UI

1. Go to your repository on GitHub
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Enter the **Name** (e.g., `WP_ADMIN_USER`)
6. Enter the **Value** (the actual secret)
7. Click **Add secret**
8. Repeat for all secrets listed above

### Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Login
gh auth login

# Add secrets one by one
gh secret set SOPS_AGE_KEY < ~/.config/sops/age/keys.txt

gh secret set MYSQL_ROOT_PASSWORD --body "$(openssl rand -base64 32)"
gh secret set MYSQL_USER --body "wordpress"
gh secret set MYSQL_PASSWORD --body "$(openssl rand -base64 24)"

gh secret set WP_ADMIN_USER --body "admin"
gh secret set WP_ADMIN_PASSWORD --body "$(openssl rand -base64 24)"
gh secret set WP_ADMIN_EMAIL --body "admin@k8s-demo.de"

gh secret set CHATBOT_API_USER --body "wordpress"
gh secret set CHATBOT_API_PASSWORD --body "$(openssl rand -base64 24)"
gh secret set CHATBOT_DEFAULT_LANGUAGE --body "de"
```

### Via Script

Save this as `add-github-secrets.sh`:

```bash
#!/bin/bash
set -e

# Repository (format: owner/repo)
REPO="alexbenisch/homelab-demo"

echo "Adding GitHub Secrets for WordPress..."

# SOPS Age Key (required - must already exist)
if [ -f ~/.config/sops/age/keys.txt ]; then
    gh secret set SOPS_AGE_KEY --repo $REPO < ~/.config/sops/age/keys.txt
    echo "✓ SOPS_AGE_KEY added"
else
    echo "✗ Age key not found at ~/.config/sops/age/keys.txt"
    exit 1
fi

# MySQL Secrets
gh secret set MYSQL_ROOT_PASSWORD --repo $REPO --body "$(openssl rand -base64 32)"
echo "✓ MYSQL_ROOT_PASSWORD generated and added"

gh secret set MYSQL_USER --repo $REPO --body "wordpress"
echo "✓ MYSQL_USER added"

gh secret set MYSQL_PASSWORD --repo $REPO --body "$(openssl rand -base64 24)"
echo "✓ MYSQL_PASSWORD generated and added"

# WordPress Admin Secrets
gh secret set WP_ADMIN_USER --repo $REPO --body "admin"
echo "✓ WP_ADMIN_USER added"

gh secret set WP_ADMIN_PASSWORD --repo $REPO --body "$(openssl rand -base64 24)"
echo "✓ WP_ADMIN_PASSWORD generated and added"

gh secret set WP_ADMIN_EMAIL --repo $REPO --body "admin@k8s-demo.de"
echo "✓ WP_ADMIN_EMAIL added"

# Chatbot Secrets
gh secret set CHATBOT_API_USER --repo $REPO --body "wordpress"
echo "✓ CHATBOT_API_USER added"

gh secret set CHATBOT_API_PASSWORD --repo $REPO --body "$(openssl rand -base64 24)"
echo "✓ CHATBOT_API_PASSWORD generated and added"

gh secret set CHATBOT_DEFAULT_LANGUAGE --repo $REPO --body "de"
echo "✓ CHATBOT_DEFAULT_LANGUAGE added"

echo ""
echo "All secrets added successfully!"
echo ""
echo "IMPORTANT: Save these generated passwords before they're lost:"
echo "Run this to retrieve them (requires GitHub CLI authentication):"
echo "  gh secret list --repo $REPO"
```

Make executable and run:
```bash
chmod +x add-github-secrets.sh
./add-github-secrets.sh
```

## Running the Workflow

### Via GitHub Web UI

1. Go to your repository on GitHub
2. Click **Actions** (top menu)
3. In the left sidebar, select **Update WordPress Secrets**
4. Click **Run workflow** (right side)
5. Select branch (usually `main`)
6. Choose update type:
   - `all` - Update all secrets (recommended for initial setup)
   - `wordpress_admin` - Update only WordPress admin secrets
   - `chatbot` - Update only chatbot secrets
   - `mysql` - Update only MySQL secrets
7. Click **Run workflow**

### Via GitHub CLI

```bash
# Run workflow to update all secrets
gh workflow run wordpress-secrets-update.yaml

# Run workflow with specific update type
gh workflow run wordpress-secrets-update.yaml -f update_type=wordpress_admin

# Check workflow status
gh run list --workflow=wordpress-secrets-update.yaml
```

### Via API

```bash
# Trigger workflow
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/alexbenisch/homelab-demo/actions/workflows/wordpress-secrets-update.yaml/dispatches \
  -d '{"ref":"main","inputs":{"update_type":"all"}}'
```

## Verification

After running the workflow:

1. **Check workflow run:**
   ```bash
   gh run list --workflow=wordpress-secrets-update.yaml
   gh run view <run-id>
   ```

2. **Verify commit:**
   ```bash
   git pull
   git log --oneline -n 1 apps/base/wordpress/secret.yaml
   ```

3. **Verify encryption:**
   ```bash
   # The file should contain ENC[...] values
   cat apps/base/wordpress/secret.yaml

   # Should show encrypted values like:
   # MYSQL_ROOT_PASSWORD: ENC[AES256_GCM,data:...,iv:...,tag:...,type:str]
   ```

4. **Test decryption (if you have SOPS configured locally):**
   ```bash
   sops -d apps/base/wordpress/secret.yaml | grep -A 10 stringData
   ```

## Updating Individual Secrets

To update a single secret:

1. **Update the GitHub Secret:**
   ```bash
   # Via CLI
   gh secret set WP_ADMIN_PASSWORD --body "new-secure-password"

   # Or via Web UI (Settings → Secrets)
   ```

2. **Run the workflow:**
   ```bash
   gh workflow run wordpress-secrets-update.yaml
   ```

3. **Workflow will automatically:**
   - Read all current secrets from GitHub
   - Re-encrypt the entire secret.yaml file
   - Commit changes to the repository

## Security Considerations

### ✅ Secure Practices

- Secrets are encrypted at rest in GitHub Secrets
- Secrets are encrypted with SOPS before committing to Git
- SOPS age key is never committed to the repository
- Workflow uses ephemeral runners (secrets cleaned up after run)
- Temporary decrypted files are removed after processing

### ⚠️ Important Notes

1. **Never commit unencrypted secrets** to Git
2. **Keep your age key secure** - without it, you cannot decrypt secrets
3. **Rotate secrets regularly** - update GitHub Secrets and re-run workflow
4. **Limit access** to GitHub repository settings (only admins should access secrets)
5. **Audit changes** - all secret updates create Git commits for tracking

## Troubleshooting

### Workflow fails with "SOPS_AGE_KEY not found"

**Solution:** Add the `SOPS_AGE_KEY` secret to GitHub:
```bash
gh secret set SOPS_AGE_KEY < ~/.config/sops/age/keys.txt
```

### Workflow fails with "failed to decrypt"

**Problem:** The age key in GitHub Secrets doesn't match the one used to encrypt the file

**Solution:**
1. Verify you're using the correct age key:
   ```bash
   # Get the public key from your age key
   age-keygen -y ~/.config/sops/age/keys.txt

   # Compare with the recipient in secret.yaml
   grep "recipient:" apps/base/wordpress/secret.yaml
   ```

2. If they don't match, you need to re-encrypt with the correct key or update the GitHub Secret

### Workflow succeeds but no changes committed

**Reason:** The secrets in GitHub Secrets match what's already in the encrypted file

**This is normal** - the workflow only commits if there are changes

### Secret not being updated

**Solution:**
1. Verify the secret exists in GitHub:
   ```bash
   gh secret list | grep WP_ADMIN_PASSWORD
   ```

2. Check the workflow logs for errors:
   ```bash
   gh run view --log
   ```

## Manual Operations

If you need to manually manage secrets (without the workflow):

### Decrypt Secret

```bash
sops -d apps/base/wordpress/secret.yaml > /tmp/secret-decrypted.yaml
```

### Edit Secret

```bash
sops apps/base/wordpress/secret.yaml
# This opens in your editor and re-encrypts on save
```

### Re-encrypt Secret

```bash
sops -e /tmp/secret-decrypted.yaml > apps/base/wordpress/secret.yaml
rm /tmp/secret-decrypted.yaml
```

## Next Steps

After setting up secrets:

1. ✅ Add all required GitHub Secrets (see list above)
2. ✅ Run the workflow to encrypt and commit secrets
3. ✅ Verify the encrypted secret.yaml file was updated
4. ✅ Deploy WordPress using the updated secrets
5. ✅ Test WordPress admin login
6. ✅ Test chatbot functionality

## References

- [SOPS Documentation](https://github.com/getsops/sops)
- [age Encryption Tool](https://github.com/FiloSottile/age)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [WordPress Redeployment Strategy](../../apps/base/wordpress/REDEPLOYMENT-STRATEGY.md)
