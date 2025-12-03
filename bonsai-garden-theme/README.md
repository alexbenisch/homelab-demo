# Bonsai Garden WordPress Theme

A beautiful zen-inspired WordPress theme designed specifically for bonsai shops with WooCommerce integration. Features natural aesthetics, responsive design, and a stunning landing page.

## Features

🌳 **Bonsai-Inspired Design** - Natural color palette with forest greens, sage, and bamboo accents
🛒 **WooCommerce Ready** - Full e-commerce support with custom product styling
📱 **Fully Responsive** - Beautiful on all devices from mobile to desktop
🎨 **Customizable** - Easy theme customizer for hero section, colors, and more
⚡ **Fast & Lightweight** - Optimized performance with minimal dependencies
♿ **Accessible** - Semantic HTML5 markup with ARIA labels
🔍 **SEO Friendly** - Clean code structure for better search rankings

## Color Palette

- **Primary (Deep Forest Green)**: `#2d5016`
- **Secondary (Sage Green)**: `#7d8f69`
- **Accent (Natural Wood)**: `#c4a57b`
- **Light (Parchment)**: `#f4f1ea`
- **Dark (Almost Black)**: `#1a1a1a`

## Requirements

- WordPress 5.8 or higher
- PHP 7.4 or higher
- WooCommerce 6.0 or higher (optional but recommended)

## Installation

### Method 1: WordPress Admin Upload

1. **Download Theme**
   ```bash
   cd /home/alex/repos/homelab-demo
   python3 -m zipfile -c bonsai-garden-theme.zip bonsai-garden-theme/
   ```

2. **Install in WordPress**
   - Go to WordPress Admin → Appearance → Themes
   - Click "Add New" → "Upload Theme"
   - Choose `bonsai-garden-theme.zip`
   - Click "Install Now"
   - Click "Activate"

### Method 2: Direct Upload via kubectl

1. **Copy theme to WordPress container**
   ```bash
   POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

   kubectl cp bonsai-garden-theme wordpress/$POD_NAME:/var/www/html/wp-content/themes/

   kubectl exec -n wordpress $POD_NAME -- chown -R www-data:www-data /var/www/html/wp-content/themes/bonsai-garden-theme
   ```

2. **Activate in WordPress**
   - Go to Appearance → Themes
   - Find "Bonsai Garden"
   - Click "Activate"

### Method 3: WP-CLI

```bash
POD_NAME=$(kubectl get pods -n wordpress -l app=wordpress -o jsonpath='{.items[0].metadata.name}')

# Copy theme
kubectl cp bonsai-garden-theme wordpress/$POD_NAME:/var/www/html/wp-content/themes/

# Activate theme
kubectl exec -n wordpress $POD_NAME -- wp theme activate bonsai-garden --allow-root
```

## Initial Setup

### 1. Set Homepage

1. Go to **Pages → Add New**
2. Create a page titled "Home" (leave content empty)
3. Go to **Settings → Reading**
4. Select "A static page"
5. Choose "Home" as your homepage
6. Save changes

### 2. Configure Menus

1. Go to **Appearance → Menus**
2. Create a menu called "Primary Menu"
3. Add pages: Home, Shop, About, Contact
4. Assign to "Primary Menu" location
5. Save menu

### 3. Customize Hero Section

1. Go to **Appearance → Customize → Hero Section**
2. Configure:
   - **Hero Title**: "Cultivate Beauty, One Tree at a Time"
   - **Hero Subtitle**: "Discover our curated collection of bonsai trees, tools, and expert care guides"
   - **Button Text**: "Explore Our Collection"
   - **Button URL**: `/shop`
3. Click "Publish"

### 4. Set Up WooCommerce

1. Install and activate WooCommerce plugin
2. Run WooCommerce setup wizard
3. Create product categories:
   - Live Bonsai Trees
   - Tools & Accessories
   - Pots & Containers
   - Care Guides
4. Add products with featured images
5. Mark 3-4 products as "Featured" for homepage display

### 5. Configure Footer Widgets (Optional)

1. Go to **Appearance → Widgets**
2. Add widgets to Footer 1, Footer 2, Footer 3:
   - **Footer 1**: Text widget with shop description
   - **Footer 2**: Navigation menu widget
   - **Footer 3**: Contact information

## Theme Customization

### Via WordPress Customizer

Go to **Appearance → Customize**:

- **Site Identity**: Upload logo, change site title
- **Hero Section**: Customize homepage hero text and button
- **Menus**: Configure navigation menus
- **Widgets**: Manage sidebar and footer widgets

### Via Code

**Colors** - Edit `style.css`:
```css
:root {
    --color-primary: #2d5016;   /* Change primary color */
    --color-secondary: #7d8f69; /* Change secondary color */
    --color-accent: #c4a57b;    /* Change accent color */
}
```

**Fonts** - Edit `functions.php`:
```php
// Change Google Fonts URL
wp_enqueue_style(
    'bonsai-garden-fonts',
    'https://fonts.googleapis.com/css2?family=YOUR-FONT-HERE',
    array(),
    null
);
```

## File Structure

```
bonsai-garden-theme/
├── style.css                   # Main stylesheet with theme header
├── functions.php               # Theme setup and functionality
├── header.php                  # Site header template
├── footer.php                  # Site footer template
├── index.php                   # Main blog/archive template
├── front-page.php              # Landing page template
├── woocommerce.php             # WooCommerce shop template
├── assets/
│   ├── css/
│   │   └── woocommerce.css     # WooCommerce-specific styles
│   └── js/
│       └── main.js             # Theme JavaScript
└── README.md                   # This file
```

## Troubleshooting

### Landing Page Not Showing

1. Go to **Settings → Reading**
2. Select "A static page" (not "Your latest posts")
3. Choose your "Home" page as Homepage
4. Save changes

### Featured Products Not Appearing

1. Edit products in WooCommerce
2. Check "Featured product" checkbox in Product Data → Catalog
3. Save product
4. Refresh homepage

### Styles Not Loading

1. Go to **Settings → Permalinks**
2. Click "Save Changes" (this refreshes rewrite rules)
3. Hard refresh browser (Ctrl+Shift+R)
4. Check that theme is activated

### Mobile Menu Not Working

1. Ensure jQuery is loaded (check browser console)
2. Clear cache
3. Check that `main.js` is enqueued in functions.php

## Features Included

### Landing Page Sections

- ✅ Hero section with customizable text and button
- ✅ Featured products carousel (3 products)
- ✅ About section with features list
- ✅ Shop by category grid (4 categories)
- ✅ Why choose us benefits (3 benefits)
- ✅ Call-to-action section

### WooCommerce Integration

- ✅ Custom product grid styling
- ✅ Single product page layout
- ✅ Shopping cart styling
- ✅ Checkout page design
- ✅ Cart icon in header with item count
- ✅ Product gallery support
- ✅ Responsive product grids

### Additional Features

- ✅ Sticky header navigation
- ✅ Smooth scroll for anchor links
- ✅ Mobile-responsive menu
- ✅ Google Fonts integration (Cinzel, Lora, Noto Sans)
- ✅ Widget-ready (sidebar + 3 footer areas)
- ✅ Custom logo support
- ✅ Post thumbnail support
- ✅ HTML5 markup
- ✅ Translation ready

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Minimal CSS (< 10KB gzipped)
- Optimized JavaScript
- Lazy-loaded images support
- No jQuery dependencies except WooCommerce
- Fast page load times

## Accessibility

- Semantic HTML5 elements
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast compliance
- Screen reader friendly

## SEO Features

- Semantic markup
- Proper heading hierarchy
- Alt tags on images
- Clean URL structure
- Schema-ready

## Support

For issues or questions:
- Check WordPress error log: `wp-content/debug.log`
- Review browser console for JavaScript errors
- Ensure all requirements are met
- Test with default WP theme to isolate issues

## License

GPL v2 or later

## Credits

**Theme**: Bonsai Garden
**Developed for**: Bonsai shop demo with WooCommerce
**Fonts**: Google Fonts (Cinzel, Lora, Noto Sans)
**Icons**: SVG icons (inline)

## Changelog

### Version 1.0.0 (2025-11-28)
- Initial release
- Landing page template
- WooCommerce integration
- Responsive design
- Theme customizer support
- Google Fonts integration
- Widget areas
- Navigation menus
- Custom CSS and JavaScript
