# WordPress Operations Guide

This document covers common operational tasks for managing the WordPress deployment in Kubernetes.

## Table of Contents

- [WP-CLI Installation](#wp-cli-installation)
- [Media Management](#media-management)
- [Theme Management](#theme-management)
- [Plugin Management](#plugin-management)
- [Database Operations](#database-operations)

---

## WP-CLI Installation

WP-CLI is not included in the default WordPress Docker image. Install it when needed:

### Install WP-CLI in Container

```bash
# Get pod name
POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

# Install WP-CLI
kubectl exec -n wordpress $POD_NAME -- bash -c "
  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && \
  chmod +x wp-cli.phar && \
  mv wp-cli.phar /usr/local/bin/wp
"

# Verify installation
kubectl exec -n wordpress $POD_NAME -- wp --info --allow-root
```

**Note:** WP-CLI installation is ephemeral and will be lost on pod restart. For persistent WP-CLI, create a custom Docker image with WP-CLI pre-installed (see `Plan-for-WP-WC-Image-Deployment.md`).

---

## Media Management

### Bulk Upload Images to WordPress

#### Step 1: Prepare Images Locally

Download or prepare your images:

```bash
# Example: Download bonsai images from Unsplash
cd /home/alex/repos/homelab-demo/product-images
./download-bonsai-images.sh

# Verify images
ls -lh bonsai/
```

#### Step 2: Upload to WordPress Container

```bash
# Get pod name
POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

# Create uploads directory
kubectl exec -n wordpress $POD_NAME -- mkdir -p /var/www/html/wp-content/uploads/bonsai-products

# Copy images to pod
kubectl cp ./bonsai wordpress/$POD_NAME:/var/www/html/wp-content/uploads/bonsai-products/

# Fix permissions
kubectl exec -n wordpress $POD_NAME -- chown -R www-data:www-data /var/www/html/wp-content/uploads/bonsai-products/
kubectl exec -n wordpress $POD_NAME -- chmod -R 755 /var/www/html/wp-content/uploads/bonsai-products/
```

#### Step 3: Register Images in WordPress Database

```bash
# Install WP-CLI (if not already installed)
kubectl exec -n wordpress $POD_NAME -- bash -c "
  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && \
  chmod +x wp-cli.phar && \
  mv wp-cli.phar /usr/local/bin/wp
"

# Import all images to Media Library
kubectl exec -n wordpress $POD_NAME -- bash -c '
cd /var/www/html/wp-content/uploads/bonsai-products/bonsai/
count=0
for img in *.jpg; do
  count=$((count + 1))
  echo "[$count] Importing: $img"
  wp media import "/var/www/html/wp-content/uploads/bonsai-products/bonsai/$img" \
    --path=/var/www/html \
    --allow-root \
    --title="Bonsai $count" \
    --alt="Bonsai tree $count" \
    --porcelain
done
'
```

#### Step 4: Verify Import

```bash
# Get MySQL root password
MYSQL_ROOT_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)

# Query database to verify
kubectl exec -n wordpress deployment/mysql -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress -e "
  SELECT ID, post_title, guid
  FROM wp_posts
  WHERE post_type='attachment'
  AND post_title LIKE 'Bonsai%'
  ORDER BY ID;
" 2>&1 | grep -v "Using a password"

# Count imported images
kubectl exec -n wordpress deployment/mysql -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress -e "
  SELECT COUNT(*) as 'Total Images'
  FROM wp_posts
  WHERE post_type='attachment'
  AND post_title LIKE 'Bonsai%';
" 2>&1 | grep -v "Using a password"
```

#### Result

Images are now:
- ✅ Uploaded to `/var/www/html/wp-content/uploads/2025/12/`
- ✅ Registered as attachments in `wp_posts` table
- ✅ Visible in WordPress Media Library: `https://wordpress.k8s-demo.de/wp-admin/upload.php`
- ✅ Thumbnails generated automatically
- ✅ Available for use in WooCommerce products

---

## Theme Management

### Upload Custom Theme

```bash
# Copy theme to pod
POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

kubectl cp /path/to/bonsai-garden-theme wordpress/$POD_NAME:/var/www/html/wp-content/themes/

# Fix permissions
kubectl exec -n wordpress $POD_NAME -- chown -R www-data:www-data /var/www/html/wp-content/themes/bonsai-garden-theme
kubectl exec -n wordpress $POD_NAME -- find /var/www/html/wp-content/themes/bonsai-garden-theme -type d -exec chmod 755 {} \;
kubectl exec -n wordpress $POD_NAME -- find /var/www/html/wp-content/themes/bonsai-garden-theme -type f -exec chmod 644 {} \;
```

### Activate Theme via WP-CLI

```bash
kubectl exec -n wordpress $POD_NAME -- wp theme activate bonsai-garden-theme --path=/var/www/html --allow-root
```

### Update Theme Files

```bash
# Copy single file (e.g., style.css)
kubectl cp /path/to/style.css wordpress/$POD_NAME:/var/www/html/wp-content/themes/bonsai-garden-theme/style.css

# Fix ownership
kubectl exec -n wordpress $POD_NAME -- chown www-data:www-data /var/www/html/wp-content/themes/bonsai-garden-theme/style.css
```

---

## Plugin Management

### Install Plugin via WP-CLI

```bash
POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

# Install and activate plugin
kubectl exec -n wordpress $POD_NAME -- wp plugin install woocommerce --activate --path=/var/www/html --allow-root

# List installed plugins
kubectl exec -n wordpress $POD_NAME -- wp plugin list --path=/var/www/html --allow-root
```

### Upload Custom Plugin

```bash
# Copy plugin directory
kubectl cp /path/to/bonsai-chatbot-plugin wordpress/$POD_NAME:/var/www/html/wp-content/plugins/

# Fix permissions
kubectl exec -n wordpress $POD_NAME -- chown -R www-data:www-data /var/www/html/wp-content/plugins/bonsai-chatbot-plugin

# Activate plugin
kubectl exec -n wordpress $POD_NAME -- wp plugin activate bonsai-chatbot-plugin --path=/var/www/html --allow-root
```

---

## Database Operations

### Access MySQL Database

```bash
# Get MySQL root password
MYSQL_ROOT_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)

# Connect to MySQL
kubectl exec -it -n wordpress deployment/mysql -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress
```

### Common Database Queries

```sql
-- List all posts
SELECT ID, post_title, post_type, post_status FROM wp_posts LIMIT 10;

-- List all media attachments
SELECT ID, post_title, guid FROM wp_posts WHERE post_type='attachment' ORDER BY ID DESC LIMIT 20;

-- List WooCommerce products
SELECT ID, post_title, post_status FROM wp_posts WHERE post_type='product';

-- Get WordPress options
SELECT option_name, option_value FROM wp_options WHERE option_name IN ('siteurl', 'home', 'template', 'stylesheet');

-- Count posts by type
SELECT post_type, COUNT(*) as count FROM wp_posts GROUP BY post_type;
```

### Backup Database

```bash
MYSQL_ROOT_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)

# Backup to local file
kubectl exec -n wordpress deployment/mysql -- mysqldump -u root -p$MYSQL_ROOT_PASSWORD wordpress > wordpress-backup-$(date +%Y%m%d-%H%M%S).sql

# Verify backup
ls -lh wordpress-backup-*.sql
```

### Restore Database

```bash
# Copy backup to pod
kubectl cp wordpress-backup-20251201.sql wordpress/mysql-xxxxx:/tmp/backup.sql

# Restore
kubectl exec -n wordpress deployment/mysql -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress < /tmp/backup.sql
```

### Clear Transients (Cache)

```bash
MYSQL_ROOT_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)

kubectl exec -n wordpress deployment/mysql -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress -e "DELETE FROM wp_options WHERE option_name LIKE '%_transient_%';"
```

---

## Troubleshooting

### Check Pod Logs

```bash
# WordPress logs
kubectl logs -n wordpress deployment/wordpress --tail=100

# MySQL logs
kubectl logs -n wordpress deployment/mysql --tail=100

# Follow logs in real-time
kubectl logs -n wordpress deployment/wordpress -f
```

### Restart Pods

```bash
# Restart WordPress
kubectl rollout restart deployment/wordpress -n wordpress

# Restart MySQL (caution: brief downtime)
kubectl rollout restart deployment/mysql -n wordpress

# Check pod status
kubectl get pods -n wordpress
```

### Fix File Permissions

```bash
POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

# Fix all WordPress file permissions
kubectl exec -n wordpress $POD_NAME -- bash -c "
  chown -R www-data:www-data /var/www/html
  find /var/www/html -type d -exec chmod 755 {} \;
  find /var/www/html -type f -exec chmod 644 {} \;
"
```

### Check WooCommerce Coming Soon Mode

```bash
MYSQL_ROOT_PASSWORD=$(kubectl get secret -n wordpress wordpress-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)

# Check status
kubectl exec -n wordpress deployment/mysql -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress -e "SELECT option_value FROM wp_options WHERE option_name='woocommerce_coming_soon';"

# Disable coming soon mode
kubectl exec -n wordpress deployment/mysql -- mysql -u root -p$MYSQL_ROOT_PASSWORD wordpress -e "UPDATE wp_options SET option_value='no' WHERE option_name='woocommerce_coming_soon';"
```

---

## References

- **WP-CLI Documentation**: https://wp-cli.org/
- **WordPress Codex**: https://codex.wordpress.org/
- **WooCommerce Docs**: https://woocommerce.com/documentation/
- **Kubernetes Documentation**: https://kubernetes.io/docs/
