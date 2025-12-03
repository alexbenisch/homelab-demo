# WooCommerce Integration Plan for WordPress Deployment

## Overview

Add WooCommerce e-commerce platform to the existing WordPress deployment to support a bonsai shop demo/testing environment. This will serve as a front-end for the Ollama chatbot testing with complex requirements including live plant sales (EU-only shipping), worldwide accessory sales, digital downloads, and integration potential with the Ollama chatbot at chat.k8s-demo.de.

**User Preferences:**
- Custom Docker image with WooCommerce pre-installed
- No Redis cache initially (add later if performance requires)
- Local SMTP for demo/testing (no external SMTP provider)
- Bank Transfer payment method only (simplest, no API keys)

## Recommended Approach: Custom Docker Image + WP-CLI Automation

### Why This Approach?

**Build a custom Docker image with WooCommerce pre-installed** + **WP-CLI init container for automated configuration**

**Rationale:**
- **GitOps Compatible**: Plugin versions tracked in Dockerfile
- **Repeatable**: Identical deployments every time
- **Fast Startup**: No plugin downloads on pod creation
- **Version Control**: Dockerfile documents exact plugin versions
- **Industry Standard**: Matches production WordPress in Kubernetes

**Trade-offs:**
- ✅ Fully declarative and version-controlled
- ✅ Production-ready and maintainable
- ✅ Easy rollback via image tags
- ❌ Requires building custom image (but already done for demo-django)
- ❌ Must rebuild for WordPress/plugin updates (standard practice)

## Architecture

```
WordPress Pod:
  - Init Container: woocommerce-setup (WP-CLI automation)
    * Waits for MySQL ready
    * Activates plugins
    * Configures basic WooCommerce settings
  - Main Container: wordpress-woocommerce:1.0
    * WordPress 6.4 + WooCommerce 8.5+
    * Pre-installed plugins
  - Optional: Redis sidecar for caching

MySQL Pod: (Existing - No Changes)
  - mysql:8.0 with 5Gi PVC

Storage:
  - wordpress-pvc: 5Gi → 10Gi (for product images)
  - mysql-pvc: 5Gi (adequate for WooCommerce)
```

## Implementation Steps

### Phase 1: Docker Image Creation

**Create:** `wordpress-woocommerce/Dockerfile`

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

# Pre-install WooCommerce and essential plugins
RUN set -ex; \
    mkdir -p /tmp/plugins; \
    wp plugin install woocommerce --version=8.5.2 --allow-root --path=/tmp/plugins; \
    wp plugin install woocommerce-pdf-invoices-packing-slips --allow-root --path=/tmp/plugins; \
    wp plugin install woocommerce-gateway-stripe --allow-root --path=/tmp/plugins; \
    wp plugin install redis-cache --allow-root --path=/tmp/plugins; \
    wp plugin install wp-mail-smtp --allow-root --path=/tmp/plugins; \
    mkdir -p /usr/src/wordpress/wp-content/plugins; \
    cp -r /tmp/plugins/* /usr/src/wordpress/wp-content/plugins/; \
    chown -R www-data:www-data /usr/src/wordpress/wp-content/plugins
```

**Build and push:**
```bash
docker build -t ghcr.io/alexbenisch/wordpress-woocommerce:1.0 ./wordpress-woocommerce/
docker push ghcr.io/alexbenisch/wordpress-woocommerce:1.0
```

### Phase 2: WP-CLI Setup Script

**Create:** `apps/base/wordpress/woocommerce-configmap.yaml`

ConfigMap with bash script that:
- Waits for MySQL and WordPress to be ready
- Activates WooCommerce and plugins
- Configures basic settings (currency, country, units)
- Sets up initial tax calculation

### Phase 3: Update Kubernetes Manifests

**Modify:** `apps/base/wordpress/deployment.yaml`
- Change image to `ghcr.io/alexbenisch/wordpress-woocommerce:1.0`
- Add init container with WP-CLI setup script
- Increase resources:
  - CPU: 100m → 200m (request), 500m → 1000m (limit)
  - Memory: 128Mi → 256Mi (request), 512Mi → 1Gi (limit)
- Add WooCommerce environment variables
- Update probes to `/wp-admin/admin-ajax.php`
- Add deployment strategy: `Recreate` (for PVC)
- Mount ConfigMap for setup script

**Modify:** `apps/base/wordpress/wordpress-pvc.yaml`
- Increase storage: 5Gi → 10Gi (for product images)
- Note: k3s local-path supports PVC expansion

**Optional:** SMTP configuration
- For demo/testing: Use WordPress default PHP mail() function
- For production-like testing: Can add MailHog container for email preview
- Skip external SMTP provider for this demo environment

**Update:** `apps/base/wordpress/kustomization.yaml`
- Add `woocommerce-configmap.yaml`

### Phase 4: Deployment Process

1. **Backup Current Installation**
   ```bash
   kubectl exec -n wordpress deployment/wordpress -- tar czf /tmp/wp-backup.tar.gz -C /var/www/html .
   kubectl cp wordpress/wordpress-xxx:/tmp/wp-backup.tar.gz ./wordpress-backup-$(date +%Y%m%d).tar.gz
   kubectl exec -n wordpress deployment/mysql -- mysqldump -u root -p$ROOT_PASSWORD wordpress > wp-db-backup.sql
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/woocommerce-integration
   ```

3. **Commit Changes**
   ```bash
   git add apps/base/wordpress/ wordpress-woocommerce/
   git commit -m "Add WooCommerce to WordPress deployment"
   git push origin feature/woocommerce-integration
   ```

4. **Deploy via GitOps**
   ```bash
   # After PR merge
   flux reconcile kustomization apps --with-source
   ```

5. **Monitor Deployment**
   ```bash
   kubectl get pods -n wordpress -w
   kubectl logs -n wordpress deployment/wordpress -c woocommerce-setup
   kubectl logs -n wordpress deployment/wordpress -c wordpress -f
   kubectl exec -n wordpress deployment/wordpress -- wp plugin list --allow-root
   ```

### Phase 5: Manual WordPress Configuration

Access: https://wordpress.k8s-demo.de/wp-admin

**Required Configuration Tasks:**

1. **WooCommerce Setup Wizard**
   - Store details and address
   - Industry: Bonsai / Plants
   - Product types: Physical, Digital, Downloads
   - Enable tax calculation

2. **Shipping Zones**
   - **EU Zone (Live Plants)**: Standard €15, Express €25
   - **Worldwide Zone (Accessories)**: Standard €20, Express €40
   - Configure category-based restrictions

3. **Product Categories**
   - Live Bonsai Trees (EU only, non-returnable)
   - Tools (Worldwide, returnable)
   - Pots & Containers (Worldwide, returnable)
   - Digital Guides (Downloadable)
   - Starter Kits (Bundles, EU only)

4. **Payment Gateway**
   - Bank Transfer: Add bank account details (demo account for testing)
   - Disable other payment methods

5. **Tax Settings**
   - Standard: 19% (Germany/EU)
   - Reduced: 7% (books/guides)
   - Zero: 0% (non-EU exports)

6. **Product Attributes**
   - Species, Age, Size, Difficulty, Indoor/Outdoor

7. **Email Templates**
   - Customize order confirmation
   - Add shop logo
   - Configure shipping notifications

### Phase 6: Sample Products

Create test products:
- **Japanese Juniper Bonsai**: €89, EU-only, non-returnable
- **Professional Tool Set**: €45, worldwide, returnable
- **Bonsai Care Guide**: €9.99, digital download
- **Beginner Starter Kit**: €129, bundle with live plant

### Phase 7: Testing

**Functional Tests:**
- Browse catalog, add to cart
- EU vs. US shipping restriction validation
- Complete test order via Bank Transfer
- Verify order created in admin
- Digital product download link generation
- Admin order management
- Inventory updates after order

**Performance Tests:**
```bash
ab -n 1000 -c 10 https://wordpress.k8s-demo.de/shop/
kubectl top pods -n wordpress
```

**Security Tests:**
- HTTPS enforcement
- Admin password requirements
- File upload restrictions
- Payment data handling
- SOPS encryption verification

## Optional Add-Ons (If Needed Later)

### Redis Cache (Performance Optimization)
If response times are slow after initial deployment, add Redis.

Configuration:
- Redis 7-alpine
- emptyDir storage (cache is ephemeral)
- 50m/200m CPU, 64Mi/256Mi memory
- Activate via: `wp redis enable --allow-root`

### MailHog (Email Testing)
For previewing order emails in demo environment without sending real emails.

Configuration:
- MailHog container for email capture
- SMTP: mailhog:1025
- Web UI: http://mailhog:8025
- Useful for testing email templates

## Resource Requirements

**Storage:**
- WordPress PVC: 5Gi → 10Gi (+100%)
- MySQL PVC: 5Gi (no change)

**Compute:**
- WordPress: 200m/1000m CPU, 256Mi/1Gi memory (+2x increase)
- MySQL: 250m/500m CPU, 256Mi/512Mi memory (no change)

## Integration with Ollama Chatbot (Future)

Enable via WooCommerce REST API:
- Generate API keys in WordPress admin
- Store in SOPS-encrypted secret for chatbot
- Chatbot can query products, check order status, calculate shipping

Example endpoints:
- `GET /wp-json/wc/v3/products` - Product queries
- `GET /wp-json/wc/v3/orders/123` - Order status
- `POST /wp-json/wc/v3/shipping/zones/1/methods` - Shipping calculator

## Success Criteria

**Functional:**
- WooCommerce activated and accessible
- Products visible in shop
- Shopping cart and checkout functional
- Payment processing works
- Shipping restrictions enforced (EU vs. worldwide)
- Digital downloads generate links
- Order emails sent
- Admin order management working
- Inventory updates after purchase

**Performance:**
- Shop page loads < 2 seconds
- No pod restarts
- CPU < 80% under normal load
- Memory < 80% under normal load
- Storage < 70% utilized

**Security:**
- All secrets SOPS-encrypted
- HTTPS enforced
- Payment data never stored locally
- Database not publicly accessible

**Operational:**
- All configuration in Git
- Deployment via Flux (GitOps)
- Rollback tested
- Documentation complete

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Plugin compatibility | Use stable WooCommerce version, test thoroughly |
| Performance degradation | Implement Redis cache, monitor resources |
| Database migration failure | Comprehensive backup, test rollback |
| Storage exhaustion | Monitor usage, alerts at 80%, expand proactively |
| Payment gateway issues | Multiple payment methods, monitor Stripe |
| Email delivery failures | Reliable SMTP provider, test sending |
| Data loss | Daily automated backups, test restore |
| Security vulnerabilities | Regular updates, WordPress security best practices |

## Rollback Strategy

If deployment fails:
1. Identify issue (logs, events)
2. Quick rollback: `git revert HEAD && git push`
3. Flux reconciles automatically
4. Verify pods
5. Restore database if needed

## Critical Files

1. **`wordpress-woocommerce/Dockerfile`** (CREATE)
   - Custom image with WooCommerce pre-installed

2. **`apps/base/wordpress/deployment.yaml`** (MODIFY)
   - Init container, updated image, increased resources

3. **`apps/base/wordpress/woocommerce-configmap.yaml`** (CREATE)
   - WP-CLI setup script for automation

4. **`apps/base/wordpress/wordpress-pvc.yaml`** (MODIFY)
   - Storage expansion 5Gi → 10Gi

5. **`apps/base/wordpress/kustomization.yaml`** (MODIFY)
   - Add new ConfigMap resource

## Timeline

Estimated: 5 days (26-36 hours)
- Day 1: Docker image, Kubernetes manifests (6-8h)
- Day 2: Deploy, monitor, initial WordPress config (6-8h)
- Day 3: WooCommerce setup, products, functional testing (6-8h)
- Day 4: Performance/security testing, optimization (4-6h)
- Day 5: Production hardening, documentation, review (4-6h)

## Next Steps

1. ✅ Plan reviewed and questions answered
2. Create feature branch: `git checkout -b feature/woocommerce-integration`
3. Create Dockerfile and build custom image
4. Push image to ghcr.io/alexbenisch/wordpress-woocommerce:1.0
5. Create WooCommerce ConfigMap with WP-CLI setup script
6. Modify deployment.yaml (init container, image, resources)
7. Expand wordpress-pvc.yaml storage to 10Gi
8. Update kustomization.yaml
9. Commit, push, and deploy via GitOps
10. Configure WooCommerce via WordPress admin
11. Create sample bonsai products
12. Test end-to-end functionality
13. Document setup for future reference

**Note:** Since this is a demo environment for chatbot testing, the setup is simplified:
- No external SMTP provider (use PHP mail or add MailHog later)
- No payment gateway API keys (Bank Transfer only)
- No Redis initially (add if performance requires)
- Focus on product catalog and integration with Ollama chatbot
