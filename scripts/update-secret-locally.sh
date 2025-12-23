#!/bin/bash
set -e

# Script to update secret.yaml locally with new secrets from .env
# This adds the missing WP_ADMIN_* and CHATBOT_* secrets

SOPS_KEY_FILE="$HOME/.config/sops/age/homelab-demo-key.txt"
SECRET_FILE="apps/base/wordpress/secret.yaml"
ENV_FILE=".env"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Update WordPress Secret File Locally"
echo "========================================="
echo ""

# Check SOPS key exists
if [ ! -f "$SOPS_KEY_FILE" ]; then
  echo -e "${RED}✗ SOPS age key not found at $SOPS_KEY_FILE${NC}"
  exit 1
fi

# Check .env exists
if [ ! -f "$ENV_FILE" ]; then
  echo -e "${RED}✗ .env file not found${NC}"
  exit 1
fi

# Check secret.yaml exists
if [ ! -f "$SECRET_FILE" ]; then
  echo -e "${RED}✗ secret.yaml not found at $SECRET_FILE${NC}"
  exit 1
fi

echo -e "${GREEN}✓ All required files found${NC}"
echo ""

# Load environment variables
set -a
source "$ENV_FILE"
set +a

echo "Decrypting current secret..."
export SOPS_AGE_KEY_FILE="$SOPS_KEY_FILE"
sops -d "$SECRET_FILE" > /tmp/secret-decrypted.yaml

echo "Adding new secrets..."

# Create updated secret with all fields
cat > /tmp/secret-updated.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
    name: wordpress-secret
type: Opaque
stringData:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    MYSQL_USER: ${MYSQL_USER}
    MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    WP_ADMIN_USER: ${WP_ADMIN_USER}
    WP_ADMIN_PASSWORD: ${WP_ADMIN_PASSWORD}
    WP_ADMIN_EMAIL: ${WP_ADMIN_EMAIL}
    CHATBOT_API_USER: ${CHATBOT_API_USER}
    CHATBOT_API_PASSWORD: ${CHATBOT_API_PASSWORD}
    CHATBOT_DEFAULT_LANGUAGE: ${CHATBOT_DEFAULT_LANGUAGE}
EOF

echo "Re-encrypting secret..."
sops -e /tmp/secret-updated.yaml > "$SECRET_FILE"

echo "Cleaning up temporary files..."
rm -f /tmp/secret-decrypted.yaml /tmp/secret-updated.yaml

echo ""
echo -e "${GREEN}✓ Secret file updated successfully!${NC}"
echo ""
echo "Updated: $SECRET_FILE"
echo ""
echo "Secrets included:"
echo "  - MYSQL_ROOT_PASSWORD"
echo "  - MYSQL_USER"
echo "  - MYSQL_PASSWORD"
echo "  - WP_ADMIN_USER (NEW)"
echo "  - WP_ADMIN_PASSWORD (NEW)"
echo "  - WP_ADMIN_EMAIL (NEW)"
echo "  - CHATBOT_API_USER (NEW)"
echo "  - CHATBOT_API_PASSWORD (NEW)"
echo "  - CHATBOT_DEFAULT_LANGUAGE (NEW)"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff $SECRET_FILE"
echo "  2. Commit the changes: git add $SECRET_FILE && git commit -m 'Add WordPress admin and chatbot secrets'"
echo "  3. Push to repository: git push"
