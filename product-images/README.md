# Product Images for Bonsai Garden

## Directory Structure

```
product-images/
└── bonsai/          # Bonsai tree product images
```

## How to Download Images from Pixabay

Since automated downloads are blocked, here are your options:

### Option 1: Manual Download (Recommended)
1. Visit https://pixabay.com/images/search/bonsai/
2. Click on each image you want
3. Click the "Free Download" button
4. Select medium or large size (1920px recommended for products)
5. Save to `product-images/bonsai/` directory
6. Name files sequentially: `bonsai-01.jpg`, `bonsai-02.jpg`, etc.

### Option 2: Use Pixabay API
```bash
# Get API key from: https://pixabay.com/api/docs/
API_KEY="your_api_key_here"

# Download images using curl
for i in {1..20}; do
  curl "https://pixabay.com/api/?key=$API_KEY&q=bonsai&image_type=photo&per_page=20&page=1" | \
  jq -r ".hits[$i].largeImageURL" | \
  xargs curl -o "product-images/bonsai/bonsai-$(printf '%02d' $i).jpg"
done
```

### Option 3: Use Unsplash (Alternative Source)
Unsplash has better API access and similar high-quality images:
```bash
# Unsplash API (requires free API key from https://unsplash.com/developers)
ACCESS_KEY="your_unsplash_key"

curl "https://api.unsplash.com/search/photos?query=bonsai&per_page=20" \
  -H "Authorization: Client-ID $ACCESS_KEY" | \
  jq -r '.results[].urls.regular' | \
  while read url; do
    wget "$url" -P product-images/bonsai/
  done
```

### Option 4: Use wget with Pixabay Direct Links
If you have the direct image URLs, you can download them:
```bash
wget -P product-images/bonsai/ "https://pixabay.com/get/[image-id].jpg"
```

## Recommended Image Specs for WooCommerce

- **Resolution**: 1200x1200px minimum (square format works best)
- **Format**: JPEG or PNG
- **File size**: Under 500KB for optimal loading
- **Naming**: Use descriptive names (e.g., `japanese-maple-bonsai.jpg`)

## Upload to WordPress

Once you have images downloaded:

```bash
# Copy to WordPress pod
kubectl cp product-images/bonsai wordpress/wordpress-xxxxx:/var/www/html/wp-content/uploads/bonsai-products/

# Or use WordPress Media Library via admin interface at:
# https://wordpress.k8s-demo.de/wp-admin/upload.php
```

## License Information

**Pixabay**: Free for commercial use, no attribution required (but appreciated)
**Unsplash**: Free for commercial use, attribution required

Always check the individual image license before using in production.
