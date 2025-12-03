#!/bin/bash
# Script to download bonsai images from Unsplash API
# Requires: curl, jq
# Usage: ./download-bonsai-images.sh

set -e

# Load environment variables
source ~/.zshenv

ACCESS_KEY="${UNSPLASH_ACCESS_KEY}"
OUTPUT_DIR="./bonsai"
SEARCH_TERM="bonsai"
NUM_IMAGES=20

# Check for API key
if [ -z "$ACCESS_KEY" ]; then
    echo "❌ Error: UNSPLASH_ACCESS_KEY not set"
    echo "Make sure your ~/.zshenv has the Unsplash credentials"
    exit 1
fi

# Check for required tools
if ! command -v curl &> /dev/null; then
    echo "❌ Error: curl is not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is not installed"
    echo "Install with: sudo pacman -S jq"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🌳 Downloading $NUM_IMAGES bonsai images from Unsplash..."
echo "📁 Output directory: $OUTPUT_DIR"
echo ""

# Fetch image data from Unsplash API
API_URL="https://api.unsplash.com/search/photos?query=$SEARCH_TERM&per_page=$NUM_IMAGES&orientation=squarish"

echo "📡 Fetching image metadata..."
RESPONSE=$(curl -s -H "Authorization: Client-ID $ACCESS_KEY" "$API_URL")

# Check if API call was successful
if echo "$RESPONSE" | jq -e '.results' > /dev/null 2>&1; then
    TOTAL_HITS=$(echo "$RESPONSE" | jq '.total')
    echo "✅ Found $TOTAL_HITS bonsai images"
    echo ""
else
    echo "❌ Error: API request failed"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

# Download images
COUNT=0
echo "$RESPONSE" | jq -r '.results[] | "\(.id)|\(.urls.regular)|\(.alt_description // "bonsai")|\(.user.name)"' | while IFS='|' read -r id url description author; do
    COUNT=$((COUNT + 1))
    FILENAME=$(printf "bonsai-%02d.jpg" $COUNT)

    echo "⬇️  [$COUNT/$NUM_IMAGES] Downloading: $FILENAME"
    echo "   Description: $description"
    echo "   Photo by: $author"

    # Download with proper attribution trigger (required by Unsplash API guidelines)
    curl -s -o "$OUTPUT_DIR/$FILENAME" "$url"

    # Trigger download tracking (required by Unsplash API terms)
    curl -s -X GET "https://api.unsplash.com/photos/$id/download" \
         -H "Authorization: Client-ID $ACCESS_KEY" > /dev/null

    if [ -f "$OUTPUT_DIR/$FILENAME" ]; then
        SIZE=$(du -h "$OUTPUT_DIR/$FILENAME" | cut -f1)
        echo "   ✅ Saved ($SIZE)"
    else
        echo "   ❌ Failed"
    fi
    echo ""

    # Rate limiting - be nice to Unsplash
    sleep 1
done

echo "🎉 Download complete!"
echo "📂 Images saved to: $OUTPUT_DIR/"
echo ""
echo "📄 Attribution: Photos provided by Unsplash"
echo "   License: Free to use (https://unsplash.com/license)"
echo ""
echo "Next steps:"
echo "1. Review images: ls -lh $OUTPUT_DIR/"
echo "2. Upload to WordPress Media Library"
echo "3. Create products in WooCommerce using these images"
