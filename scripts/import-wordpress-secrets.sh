#!/bin/bash
set -e

# WordPress Secrets Import Script
# Imports secrets from .env file to GitHub repository secrets

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "WordPress Secrets Import to GitHub"
echo "========================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &>/dev/null; then
  echo -e "${RED}✗ GitHub CLI (gh) is not installed${NC}"
  echo "Install it from: https://cli.github.com/"
  exit 1
fi

# Check if authenticated
if ! gh auth status &>/dev/null; then
  echo -e "${RED}✗ Not authenticated with GitHub CLI${NC}"
  echo "Run: gh auth login"
  exit 1
fi

# Get repository from git remote
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
  echo -e "${RED}✗ Could not determine repository${NC}"
  echo "Make sure you're in a git repository with a GitHub remote"
  exit 1
fi

echo -e "Repository: ${GREEN}$REPO${NC}"
echo ""

# Check if .env file exists
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  echo -e "${RED}✗ .env file not found${NC}"
  echo "Expected location: $ENV_FILE"
  exit 1
fi

echo -e "${GREEN}✓ Found .env file${NC}"
echo ""

# Source the .env file to get variables
set -a
source "$ENV_FILE"
set +a

# Check if SOPS age key exists
SOPS_KEY_FILE="$HOME/.config/sops/age/homelab-demo-key.txt"
if [ ! -f "$SOPS_KEY_FILE" ]; then
  echo -e "${YELLOW}⚠ SOPS age key not found at $SOPS_KEY_FILE${NC}"
  echo "The SOPS_AGE_KEY secret must be added manually."
  echo ""
  read -p "Do you want to continue without SOPS_AGE_KEY? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
  SKIP_SOPS_KEY=true
else
  SKIP_SOPS_KEY=false
fi

echo "Adding secrets to GitHub repository: $REPO"
echo ""

# Function to add secret
add_secret() {
  local name=$1
  local value=$2

  if [ -z "$value" ]; then
    echo -e "${YELLOW}⚠ $name is empty, skipping${NC}"
    return
  fi

  if gh secret set "$name" --body "$value" --repo "$REPO" 2>/dev/null; then
    echo -e "${GREEN}✓ $name${NC}"
  else
    echo -e "${RED}✗ $name (failed)${NC}"
  fi
}

# Add SOPS age key first (if available)
if [ "$SKIP_SOPS_KEY" = false ]; then
  echo "Adding SOPS_AGE_KEY..."
  if gh secret set SOPS_AGE_KEY --repo "$REPO" <"$SOPS_KEY_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ SOPS_AGE_KEY${NC}"
  else
    echo -e "${RED}✗ SOPS_AGE_KEY (failed)${NC}"
  fi
  echo ""
fi

# Add MySQL secrets
echo "Adding MySQL secrets..."
add_secret "MYSQL_ROOT_PASSWORD" "$MYSQL_ROOT_PASSWORD"
add_secret "MYSQL_USER" "$MYSQL_USER"
add_secret "MYSQL_PASSWORD" "$MYSQL_PASSWORD"
echo ""

# Add WordPress admin secrets
echo "Adding WordPress admin secrets..."
add_secret "WP_ADMIN_USER" "$WP_ADMIN_USER"
add_secret "WP_ADMIN_PASSWORD" "$WP_ADMIN_PASSWORD"
add_secret "WP_ADMIN_EMAIL" "$WP_ADMIN_EMAIL"
echo ""

# Add chatbot secrets
echo "Adding chatbot secrets..."
add_secret "CHATBOT_API_USER" "$CHATBOT_API_USER"
add_secret "CHATBOT_API_PASSWORD" "$CHATBOT_API_PASSWORD"
add_secret "CHATBOT_DEFAULT_LANGUAGE" "$CHATBOT_DEFAULT_LANGUAGE"
echo ""

echo "========================================="
echo -e "${GREEN}✓ Secrets import completed!${NC}"
echo "========================================="
echo ""

# List secrets to verify
echo "Verifying secrets..."
echo ""
gh secret list --repo "$REPO"
echo ""

# Offer to run the workflow
echo "Next step: Run the workflow to encrypt and commit secrets"
echo ""
read -p "Do you want to run the wordpress-secrets-update workflow now? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
  echo ""
  echo "Running workflow..."
  if gh workflow run wordpress-secrets-update.yaml --repo "$REPO"; then
    echo -e "${GREEN}✓ Workflow triggered successfully${NC}"
    echo ""
    echo "Monitor the workflow:"
    echo "  gh run list --workflow=wordpress-secrets-update.yaml --limit 1"
    echo "  gh run watch"
    echo ""
    echo "Or view in browser:"
    echo "  gh workflow view wordpress-secrets-update.yaml --web"
  else
    echo -e "${RED}✗ Failed to trigger workflow${NC}"
    echo "You can run it manually:"
    echo "  gh workflow run wordpress-secrets-update.yaml"
  fi
else
  echo ""
  echo "Workflow not triggered. Run it manually when ready:"
  echo "  gh workflow run wordpress-secrets-update.yaml"
  echo ""
  echo "Or via GitHub web UI:"
  echo "  Actions → Update WordPress Secrets → Run workflow"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
