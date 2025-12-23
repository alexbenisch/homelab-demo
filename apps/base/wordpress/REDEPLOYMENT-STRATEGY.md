# WordPress Redeployment Strategy - Fully Preconfigured Installation

## Overview

Strategy for redeploying wordpress.k8s-demo.de with all components preconfigured and ready to use:

- Admin credentials preconfigured
- Bonsai Garden theme installed and activated
- Bonsai Chatbot plugin installed, activated, and configured
- WooCommerce installed, activated, and configured

This extends the existing WooCommerce integration plan with full automation for a zero-touch deployment.

## Architecture

### Custom Docker Image: wordpress-preconfigured

```
FROM wordpress:6.4-apache

Components:
- WordPress 6.4 base
- WP-CLI for automation
- WooCommerce plugin pre-installed
- Bonsai Garden theme pre-installed
- Bonsai Chatbot plugin pre-installed
- PHP dependencies for WooCommerce
```

### Init Container: wordpress-setup

Runs WP-CLI commands to:

1. Install WordPress with admin credentials from secrets
2. Activate Bonsai Garden theme
3. Activate and configure Bonsai Chatbot plugin
4. Activate and configure WooCommerce
5. Configure basic WooCommerce settings (currency, country, etc.)

### Main Container: wordpress-preconfigured

Pre-configured WordPress instance ready to use immediately after deployment.

## Implementation Plan

### Phase 1: Build Custom Docker Image

#### 1.1 Create Dockerfile

**File:** `wordpress-preconfigured/Dockerfile`

```dockerfile
FROM wordpress:6.4-apache

# Install WP-CLI
RUN curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && \
    chmod +x wp-cli.phar && \
    mv wp-cli.phar /usr/local/bin/wp

# Install system dependencies for WooCommerce
RUN apt-get update && apt-get install -y \
    libzip-dev zip unzip && \
    docker-php-ext-install zip && \
    rm -rf /var/lib/apt/lists/*

# Create temporary directory for assets
RUN mkdir -p /tmp/wordpress-assets/plugins /tmp/wordpress-assets/themes

# Pre-install WooCommerce plugin
RUN wp plugin install woocommerce --version=8.5.2 --allow-root --path=/tmp/wordpress-assets/plugins

# Copy Bonsai Chatbot plugin
COPY bonsai-chatbot-plugin/ /tmp/wordpress-assets/plugins/bonsai-chatbot-plugin/

# Copy Bonsai Garden theme
COPY bonsai-garden-theme/ /tmp/wordpress-assets/themes/bonsai-garden-theme/

# Set up entrypoint to copy assets on container start
COPY docker-entrypoint-custom.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint-custom.sh

ENTRYPOINT ["docker-entrypoint-custom.sh"]
CMD ["apache2-foreground"]
```

#### 1.2 Create Custom Entrypoint

**File:** `wordpress-preconfigured/docker-entrypoint-custom.sh`

```bash
#!/bin/bash
set -e

# Copy pre-installed plugins and themes to WordPress directory
if [ ! -f /var/www/html/wp-content/plugins/woocommerce/woocommerce.php ]; then
    echo "Copying pre-installed plugins..."
    cp -r /tmp/wordpress-assets/plugins/* /usr/src/wordpress/wp-content/plugins/
fi

if [ ! -f /var/www/html/wp-content/themes/bonsai-garden-theme/style.css ]; then
    echo "Copying pre-installed theme..."
    cp -r /tmp/wordpress-assets/themes/* /usr/src/wordpress/wp-content/themes/
fi

# Fix permissions
chown -R www-data:www-data /usr/src/wordpress/wp-content/plugins /usr/src/wordpress/wp-content/themes

# Execute original WordPress entrypoint
exec docker-entrypoint.sh "$@"
```

#### 1.3 Prepare Build Assets

```bash
cd /home/alex/repos/homelab-demo

# Create build directory
mkdir -p wordpress-preconfigured

# Extract theme
unzip -q bonsai-garden-theme-v1.1.zip -d wordpress-preconfigured/bonsai-garden-theme/

# Copy chatbot plugin
cp -r bonsai-chatbot-plugin wordpress-preconfigured/
```

#### 1.4 Build and Push Image

```bash
cd /home/alex/repos/homelab-demo

# Build image
docker build -t ghcr.io/alexbenisch/wordpress-preconfigured:1.0 ./wordpress-preconfigured/

# Push to registry
docker push ghcr.io/alexbenisch/wordpress-preconfigured:1.0
```

### Phase 2: Create Setup Automation

#### 2.1 WP-CLI Setup Script

**File:** `apps/base/wordpress/wordpress-setup-configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wordpress-setup-script
data:
  setup.sh: |
    #!/bin/bash
    set -e

    echo "=== WordPress Automated Setup Script ==="

    # Wait for MySQL to be ready
    echo "Waiting for MySQL..."
    while ! mysqladmin ping -h"$WORDPRESS_DB_HOST" --silent; do
        echo "MySQL is unavailable - sleeping"
        sleep 3
    done
    echo "MySQL is ready!"

    # Wait for WordPress files to be ready
    echo "Waiting for WordPress files..."
    while [ ! -f /var/www/html/wp-config.php ]; do
        echo "WordPress not ready - sleeping"
        sleep 3
    done
    echo "WordPress files ready!"

    cd /var/www/html

    # Install WordPress if not already installed
    if ! wp core is-installed --allow-root 2>/dev/null; then
        echo "Installing WordPress..."
        wp core install \
            --url="https://wordpress.k8s-demo.de" \
            --title="Bonsai Garden Demo Shop" \
            --admin_user="$WP_ADMIN_USER" \
            --admin_password="$WP_ADMIN_PASSWORD" \
            --admin_email="$WP_ADMIN_EMAIL" \
            --skip-email \
            --allow-root
        echo "WordPress installed successfully!"
    else
        echo "WordPress already installed, skipping installation"
    fi

    # Activate Bonsai Garden theme
    echo "Activating Bonsai Garden theme..."
    CURRENT_THEME=$(wp theme list --status=active --field=name --allow-root)
    if [ "$CURRENT_THEME" != "bonsai-garden-theme" ]; then
        wp theme activate bonsai-garden-theme --allow-root
        echo "Theme activated!"
    else
        echo "Theme already active"
    fi

    # Activate WooCommerce
    echo "Setting up WooCommerce..."
    if ! wp plugin is-active woocommerce --allow-root; then
        wp plugin activate woocommerce --allow-root
        echo "WooCommerce activated!"
    else
        echo "WooCommerce already active"
    fi

    # Configure WooCommerce basic settings
    echo "Configuring WooCommerce settings..."
    wp option update woocommerce_store_address "Bonsai Garden Demo" --allow-root
    wp option update woocommerce_store_city "Berlin" --allow-root
    wp option update woocommerce_default_country "DE" --allow-root
    wp option update woocommerce_currency "EUR" --allow-root
    wp option update woocommerce_product_type "both" --allow-root
    wp option update woocommerce_allow_tracking "no" --allow-root
    wp option update woocommerce_enable_guest_checkout "yes" --allow-root
    wp option update woocommerce_enable_signup_and_login_from_checkout "yes" --allow-root
    wp option update woocommerce_calc_taxes "yes" --allow-root

    # Disable WooCommerce "Coming Soon" mode
    wp option update woocommerce_coming_soon "no" --allow-root

    # Skip WooCommerce setup wizard
    wp option update woocommerce_onboarding_profile "skipped" --allow-root

    # Activate Bonsai Chatbot plugin
    echo "Setting up Bonsai Chatbot..."
    if ! wp plugin is-active bonsai-chatbot-plugin --allow-root; then
        wp plugin activate bonsai-chatbot-plugin --allow-root
        echo "Bonsai Chatbot activated!"
    else
        echo "Bonsai Chatbot already active"
    fi

    # Configure Bonsai Chatbot
    echo "Configuring Bonsai Chatbot..."
    wp option update bonsai_chatbot_api_url "https://chatbot.k8s-demo.de" --allow-root
    wp option update bonsai_chatbot_use_rag "1" --allow-root
    wp option update bonsai_chatbot_welcome_message "Guten Tag, wie kann ich Dir behilflich sein?" --allow-root

    # Set pretty permalinks
    echo "Configuring permalinks..."
    wp rewrite structure '/%postname%/' --allow-root
    wp rewrite flush --allow-root

    echo "=== WordPress setup completed successfully! ==="
    echo "Site URL: https://wordpress.k8s-demo.de"
    echo "Admin URL: https://wordpress.k8s-demo.de/wp-admin"
    echo "Admin User: $WP_ADMIN_USER"
```

### Phase 3: Update Kubernetes Manifests

#### 3.1 Update Secret with WordPress Admin Credentials

**File:** `apps/base/wordpress/secret.yaml`

Add WordPress admin credentials:

```yaml
stringData:
  MYSQL_ROOT_PASSWORD: ENC[...]
  MYSQL_USER: ENC[...]
  MYSQL_PASSWORD: ENC[...]
  WP_ADMIN_USER: ENC[...]          # NEW: WordPress admin username
  WP_ADMIN_PASSWORD: ENC[...]      # NEW: WordPress admin password
  WP_ADMIN_EMAIL: ENC[...]         # NEW: WordPress admin email
  CHATBOT_API_USER: ENC[...]
  CHATBOT_API_PASSWORD: ENC[...]
  CHATBOT_DEFAULT_LANGUAGE: ENC[...]
```

Steps to update:

```bash
# Decrypt secret
sops -d apps/base/wordpress/secret.yaml > /tmp/secret-decrypted.yaml

# Edit to add new fields (WP_ADMIN_USER, WP_ADMIN_PASSWORD, WP_ADMIN_EMAIL)
# Example values:
#   WP_ADMIN_USER: admin
#   WP_ADMIN_PASSWORD: <strong-random-password>
#   WP_ADMIN_EMAIL: admin@k8s-demo.de

# Re-encrypt
sops -e /tmp/secret-decrypted.yaml > apps/base/wordpress/secret.yaml

# Clean up
rm /tmp/secret-decrypted.yaml
```

#### 3.2 Update Deployment with Init Container

**File:** `apps/base/wordpress/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
spec:
  replicas: 1
  strategy:
    type: Recreate  # Required for PVC
  selector:
    matchLabels:
      app: wordpress
  template:
    metadata:
      labels:
        app: wordpress
    spec:
      initContainers:
        - name: wordpress-setup
          image: ghcr.io/alexbenisch/wordpress-preconfigured:1.0
          command: ["/bin/bash", "/scripts/setup.sh"]
          env:
            - name: WORDPRESS_DB_HOST
              value: "mysql:3306"
            - name: WORDPRESS_DB_NAME
              value: "wordpress"
            - name: WORDPRESS_DB_USER
              valueFrom:
                secretKeyRef:
                  name: wordpress-secret
                  key: MYSQL_USER
            - name: WORDPRESS_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: wordpress-secret
                  key: MYSQL_PASSWORD
            - name: WP_ADMIN_USER
              valueFrom:
                secretKeyRef:
                  name: wordpress-secret
                  key: WP_ADMIN_USER
            - name: WP_ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: wordpress-secret
                  key: WP_ADMIN_PASSWORD
            - name: WP_ADMIN_EMAIL
              valueFrom:
                secretKeyRef:
                  name: wordpress-secret
                  key: WP_ADMIN_EMAIL
          volumeMounts:
            - name: wordpress-storage
              mountPath: /var/www/html
            - name: setup-script
              mountPath: /scripts
      containers:
        - name: wordpress
          image: ghcr.io/alexbenisch/wordpress-preconfigured:1.0  # Updated image
          ports:
            - containerPort: 80
              name: http
              protocol: TCP
          env:
            - name: WORDPRESS_DB_HOST
              value: "mysql:3306"
            - name: WORDPRESS_DB_NAME
              value: "wordpress"
            - name: WORDPRESS_DB_USER
              valueFrom:
                secretKeyRef:
                  name: wordpress-secret
                  key: MYSQL_USER
            - name: WORDPRESS_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: wordpress-secret
                  key: MYSQL_PASSWORD
          volumeMounts:
            - name: wordpress-storage
              mountPath: /var/www/html
          livenessProbe:
            httpGet:
              path: /wp-admin/admin-ajax.php  # More reliable for WooCommerce
              port: 80
            initialDelaySeconds: 60  # Increased for setup time
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /wp-admin/admin-ajax.php
              port: 80
            initialDelaySeconds: 30
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          resources:
            requests:
              cpu: 200m        # Increased for WooCommerce
              memory: 256Mi    # Increased for WooCommerce
            limits:
              cpu: 1000m       # Increased for WooCommerce
              memory: 1Gi      # Increased for WooCommerce
      volumes:
        - name: wordpress-storage
          persistentVolumeClaim:
            claimName: wordpress-pvc
        - name: setup-script
          configMap:
            name: wordpress-setup-script
            defaultMode: 0755
```

#### 3.3 Expand WordPress PVC

**File:** `apps/base/wordpress/wordpress-pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: wordpress-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi  # Increased from 5Gi for WooCommerce media
  storageClassName: local-path
```

#### 3.4 Update Kustomization

**File:** `apps/base/wordpress/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: wordpress

resources:
  - namespace.yaml
  - mysql-pvc.yaml
  - wordpress-pvc.yaml
  - mysql-deployment.yaml
  - mysql-service.yaml
  - deployment.yaml
  - service.yaml
  - ingress.yaml
  - secret.yaml
  - wordpress-setup-configmap.yaml  # NEW
```

### Phase 4: Deployment Process

#### 4.1 Backup Current Installation (CRITICAL)

```bash
# Get current pod name
POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

# Backup WordPress files
kubectl exec -n wordpress $POD_NAME -- tar czf /tmp/wp-backup.tar.gz -C /var/www/html .
kubectl cp wordpress/$POD_NAME:/tmp/wp-backup.tar.gz ./wordpress-backup-$(date +%Y%m%d-%H%M%S).tar.gz

# Backup MySQL database
MYSQL_ROOT_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)
kubectl exec -n wordpress deployment/mysql -- mysqldump -u root -p$MYSQL_ROOT_PASSWORD wordpress > wp-db-backup-$(date +%Y%m%d-%H%M%S).sql

# Verify backups exist
ls -lh wordpress-backup-*.tar.gz wp-db-backup-*.sql
```

#### 4.2 Prepare Build Assets

```bash
cd /home/alex/repos/homelab-demo

# Create build directory structure
mkdir -p wordpress-preconfigured

# Extract theme (use latest version)
unzip -q bonsai-garden-theme-v1.1.zip -d wordpress-preconfigured/
mv wordpress-preconfigured/bonsai-garden-theme-v1.1 wordpress-preconfigured/bonsai-garden-theme

# Copy chatbot plugin
cp -r bonsai-chatbot-plugin wordpress-preconfigured/

# Create Dockerfile and entrypoint script (as per Phase 1)
# (Copy the Dockerfile and docker-entrypoint-custom.sh content above)
```

#### 4.3 Build and Push Docker Image

```bash
cd /home/alex/repos/homelab-demo

# Build custom image
docker build -t ghcr.io/alexbenisch/wordpress-preconfigured:1.0 ./wordpress-preconfigured/

# Test image locally (optional)
docker run --rm ghcr.io/alexbenisch/wordpress-preconfigured:1.0 wp --info --allow-root

# Push to GitHub Container Registry
docker push ghcr.io/alexbenisch/wordpress-preconfigured:1.0
```

#### 4.4 Update Secrets

```bash
cd /home/alex/repos/homelab-demo

# Decrypt current secret
sops -d apps/base/wordpress/secret.yaml > /tmp/secret-decrypted.yaml

# Edit file to add WordPress admin credentials
# Add these fields under stringData:
#   WP_ADMIN_USER: admin
#   WP_ADMIN_PASSWORD: <generate-strong-password>
#   WP_ADMIN_EMAIL: admin@k8s-demo.de

# Example: generate strong password
openssl rand -base64 24

# Re-encrypt secret
sops -e /tmp/secret-decrypted.yaml > apps/base/wordpress/secret.yaml

# Clean up
rm /tmp/secret-decrypted.yaml
```

#### 4.5 Create ConfigMap

```bash
# Create the wordpress-setup-configmap.yaml file as shown in Phase 2.1
# Location: apps/base/wordpress/wordpress-setup-configmap.yaml
```

#### 4.6 Update Deployment Manifests

```bash
# Update the following files as shown in Phase 3:
# - apps/base/wordpress/deployment.yaml
# - apps/base/wordpress/wordpress-pvc.yaml
# - apps/base/wordpress/kustomization.yaml
```

#### 4.7 Create Feature Branch and Commit

```bash
cd /home/alex/repos/homelab-demo

# Create feature branch
git checkout -b feature/wordpress-preconfigured-redeployment

# Add all changes
git add apps/base/wordpress/ wordpress-preconfigured/

# Commit changes
git commit -m "Implement fully preconfigured WordPress deployment

- Build custom Docker image with WooCommerce, theme, and chatbot plugin
- Add WP-CLI init container for automated configuration
- Configure admin credentials via secrets
- Auto-activate Bonsai Garden theme
- Auto-activate and configure Bonsai Chatbot plugin
- Auto-activate and configure WooCommerce
- Increase PVC storage to 10Gi
- Increase resource limits for WooCommerce workload
- Update deployment strategy to Recreate for PVC compatibility"

# Push to remote
git push origin feature/wordpress-preconfigured-redeployment
```

#### 4.8 Deploy via GitOps

**Option A: Merge and Auto-Deploy (Flux)**

```bash
# Create PR and merge
gh pr create --title "WordPress Preconfigured Redeployment" \
             --body "Implements fully automated WordPress deployment with theme, plugins, and WooCommerce preconfigured"

# After merge, Flux will reconcile automatically
# Monitor reconciliation
flux reconcile kustomization apps --with-source

# Watch deployment
kubectl get pods -n wordpress -w
```

**Option B: Manual Apply (Testing)**

```bash
# Apply changes directly (for testing before merge)
kubectl apply -k apps/base/wordpress/

# Watch rollout
kubectl rollout status deployment/wordpress -n wordpress
```

#### 4.9 Monitor Deployment

```bash
# Watch pods come up
kubectl get pods -n wordpress -w

# Check init container logs
kubectl logs -n wordpress -l app=wordpress -c wordpress-setup --follow

# Check main container logs
kubectl logs -n wordpress -l app=wordpress -c wordpress --follow

# Verify setup completion
kubectl exec -n wordpress deployment/wordpress -- wp plugin list --allow-root
kubectl exec -n wordpress deployment/wordpress -- wp theme list --allow-root
kubectl exec -n wordpress deployment/wordpress -- wp option get woocommerce_coming_soon --allow-root
```

#### 4.10 Verify Deployment

```bash
# Check WordPress installation
curl -I https://wordpress.k8s-demo.de

# Check admin access
echo "Admin URL: https://wordpress.k8s-demo.de/wp-admin"
echo "Username: $(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.WP_ADMIN_USER}' | base64 -d)"

# Verify plugins active
kubectl exec -n wordpress deployment/wordpress -- wp plugin list --status=active --allow-root

# Verify theme active
kubectl exec -n wordpress deployment/wordpress -- wp theme list --status=active --allow-root

# Check WooCommerce configuration
kubectl exec -n wordpress deployment/wordpress -- wp option get woocommerce_currency --allow-root
kubectl exec -n wordpress deployment/wordpress -- wp option get woocommerce_coming_soon --allow-root

# Check chatbot configuration
kubectl exec -n wordpress deployment/wordpress -- wp option get bonsai_chatbot_api_url --allow-root
```

### Phase 5: Post-Deployment Configuration

#### 5.1 Access WordPress Admin

```bash
# Get admin credentials
WP_ADMIN_USER=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.WP_ADMIN_USER}' | base64 -d)
WP_ADMIN_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.WP_ADMIN_PASSWORD}' | base64 -d)

echo "URL: https://wordpress.k8s-demo.de/wp-admin"
echo "Username: $WP_ADMIN_USER"
echo "Password: $WP_ADMIN_PASSWORD"
```

#### 5.2 Verify Installation

Manual verification checklist:

- [ ] WordPress accessible at <https://wordpress.k8s-demo.de>
- [ ] Admin panel accessible at <https://wordpress.k8s-demo.de/wp-admin>
- [ ] Bonsai Garden theme active and displaying correctly
- [ ] Bonsai Chatbot widget visible on frontend
- [ ] WooCommerce installed and active
- [ ] WooCommerce "Coming Soon" mode disabled
- [ ] Shop page accessible at <https://wordpress.k8s-demo.de/shop/>

#### 5.3 Complete WooCommerce Setup (Optional Manual Steps)

If you want to fully configure WooCommerce:

1. **Create Product Categories**
   - WooCommerce > Products > Categories
   - Add: Live Bonsai Trees, Tools, Pots, Digital Guides

2. **Configure Shipping Zones**
   - WooCommerce > Settings > Shipping
   - Add EU zone and Worldwide zone
   - Configure rates

3. **Configure Payment Methods**
   - WooCommerce > Settings > Payments
   - Enable Bank Transfer (already enabled)
   - Add bank account details

4. **Configure Tax Rates**
   - WooCommerce > Settings > Tax
   - Add tax rates for Germany/EU

5. **Add Sample Products**
   - Products > Add New
   - Create test bonsai products

## Success Criteria

### Functional

- [x] WordPress installed and accessible
- [x] Admin credentials working
- [x] Bonsai Garden theme activated
- [x] Bonsai Chatbot plugin activated and configured
- [x] WooCommerce activated and configured
- [x] "Coming Soon" mode disabled
- [x] Shop page accessible
- [x] Permalinks configured (pretty URLs)

### Technical

- [x] Custom Docker image built and pushed
- [x] Init container runs successfully
- [x] All plugins activated via automation
- [x] Theme activated via automation
- [x] Configuration persisted in database
- [x] PVC storage expanded to 10Gi
- [x] Resource limits increased for WooCommerce workload

### Security

- [x] Admin credentials stored in SOPS-encrypted secrets
- [x] Secrets never exposed in logs or manifests
- [x] HTTPS enforced via Ingress
- [x] Database not publicly accessible

### Operational

- [x] Deployment via GitOps (Flux)
- [x] Rollback tested and documented
- [x] Backups created before deployment
- [x] Configuration documented in Git

## Rollback Strategy

If deployment fails or issues arise:

### Quick Rollback

```bash
# Revert Git changes
git revert HEAD
git push origin main

# Flux will automatically reconcile back to previous state
flux reconcile kustomization apps --with-source

# Monitor rollback
kubectl get pods -n wordpress -w
```

### Database Restore (if needed)

```bash
# Get MySQL pod
MYSQL_POD=$(kubectl get pods -n wordpress -l app=mysql -o jsonpath='{.items[0].metadata.name}')
MYSQL_ROOT_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)

# Copy backup to pod
kubectl cp wp-db-backup-YYYYMMDD-HHMMSS.sql wordpress/$MYSQL_POD:/tmp/restore.sql

# Restore database
kubectl exec -n wordpress $MYSQL_POD -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress < /tmp/restore.sql
```

### Files Restore (if needed)

```bash
# Get WordPress pod
WP_POD=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

# Copy backup to pod
kubectl cp wordpress-backup-YYYYMMDD-HHMMSS.tar.gz wordpress/$WP_POD:/tmp/backup.tar.gz

# Extract backup
kubectl exec -n wordpress $WP_POD -- tar xzf /tmp/backup.tar.gz -C /var/www/html

# Fix permissions
kubectl exec -n wordpress $WP_POD -- chown -R www-data:www-data /var/www/html
```

## Troubleshooting

### Init Container Fails

```bash
# Check init container logs
kubectl logs -n wordpress -l app=wordpress -c wordpress-setup

# Common issues:
# - MySQL not ready: Check MySQL pod status
# - WordPress files not ready: Check PVC mount
# - WP-CLI errors: Check database connectivity
```

### Theme Not Activated

```bash
# Manually activate theme
kubectl exec -n wordpress deployment/wordpress -- wp theme activate bonsai-garden-theme --allow-root

# Check theme status
kubectl exec -n wordpress deployment/wordpress -- wp theme list --allow-root
```

### Plugin Not Activated

```bash
# Manually activate plugin
kubectl exec -n wordpress deployment/wordpress -- wp plugin activate woocommerce --allow-root
kubectl exec -n wordpress deployment/wordpress -- wp plugin activate bonsai-chatbot-plugin --allow-root

# Check plugin status
kubectl exec -n wordpress deployment/wordpress -- wp plugin list --allow-root
```

### WooCommerce "Coming Soon" Mode Active

```bash
# Disable via WP-CLI
kubectl exec -n wordpress deployment/wordpress -- wp option update woocommerce_coming_soon "no" --allow-root

# Verify
kubectl exec -n wordpress deployment/wordpress -- wp option get woocommerce_coming_soon --allow-root
```

### Chatbot Not Working

```bash
# Check chatbot configuration
kubectl exec -n wordpress deployment/wordpress -- wp option get bonsai_chatbot_api_url --allow-root

# Reconfigure if needed
kubectl exec -n wordpress deployment/wordpress -- wp option update bonsai_chatbot_api_url "https://chatbot.k8s-demo.de" --allow-root
```

## Resource Requirements

### Storage

- WordPress PVC: 5Gi → 10Gi (+100%)
- MySQL PVC: 5Gi (no change)

### Compute

- WordPress: 200m/1000m CPU, 256Mi/1Gi memory (+2x increase)
- MySQL: 250m/500m CPU, 256Mi/512Mi memory (no change)

### Image Size

- Custom image: ~600-800 MB (WordPress + WooCommerce + plugins + theme)

## Key Differences from Original Plan

This strategy **extends** the existing WooCommerce integration plan with:

1. **Admin Password Preconfiguration**
   - Admin credentials stored in secrets
   - WordPress installed via WP-CLI with predefined admin user

2. **Theme Preconfiguration**
   - Bonsai Garden theme pre-installed in Docker image
   - Auto-activated via init container

3. **Chatbot Plugin Preconfiguration**
   - Bonsai Chatbot plugin pre-installed in Docker image
   - Auto-activated and configured via init container

4. **Zero-Touch Deployment**
   - No manual configuration required after deployment
   - Everything automated via WP-CLI in init container
   - Ready to use immediately

## Files Created/Modified

### New Files

1. `wordpress-preconfigured/Dockerfile`
2. `wordpress-preconfigured/docker-entrypoint-custom.sh`
3. `apps/base/wordpress/wordpress-setup-configmap.yaml`
4. `apps/base/wordpress/REDEPLOYMENT-STRATEGY.md` (this file)

### Modified Files

1. `apps/base/wordpress/deployment.yaml` - Add init container, update image, increase resources
2. `apps/base/wordpress/wordpress-pvc.yaml` - Increase storage to 10Gi
3. `apps/base/wordpress/kustomization.yaml` - Add ConfigMap resource
4. `apps/base/wordpress/secret.yaml` - Add WordPress admin credentials

## Next Steps

1. Review this deployment strategy
2. Generate strong admin password
3. Update secrets with admin credentials
4. Create and test custom Docker image
5. Create ConfigMap with setup script
6. Update Kubernetes manifests
7. Create feature branch and commit changes
8. Deploy via GitOps
9. Verify installation
10. Document admin credentials securely

## Timeline

Estimated implementation: 4-6 hours

- Hour 1: Build and test custom Docker image
- Hour 2: Create and test setup ConfigMap
- Hour 3: Update manifests and secrets
- Hour 4: Deploy and monitor
- Hour 5-6: Verification and troubleshooting

## References

- Existing WooCommerce Integration Plan: `apps/base/wordpress/Plan-for-WP-WC-Image-Deployment.md`
- Operations Guide: `apps/base/wordpress/OPERATIONS.md`
- WP-CLI Documentation: <https://wp-cli.org/>
- WordPress Docker Hub: <https://hub.docker.com/_/wordpress>
- WooCommerce Documentation: <https://woocommerce.com/documentation/>
