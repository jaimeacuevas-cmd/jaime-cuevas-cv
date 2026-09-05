#!/bin/bash
# Script to vendor external CDN dependencies locally
# Run this on your local machine with internet access

set -e

echo "=== Vendorizing CDN Dependencies ==="

# Create directories
mkdir -p lib/d3 lib/leaflet/images

# Download D3.js v7
echo "Downloading D3.js v7..."
curl -o lib/d3/d3.v7.min.js https://d3js.org/d3.v7.min.js
echo "✓ D3.js downloaded"

# Download Leaflet files
echo "Downloading Leaflet 1.9.4..."
curl -o lib/leaflet/leaflet.min.js https://unpkg.com/leaflet@1.9.4/dist/leaflet.min.js
curl -o lib/leaflet/leaflet.min.css https://unpkg.com/leaflet@1.9.4/dist/leaflet.min.css
echo "✓ Leaflet JS and CSS downloaded"

# Download Leaflet images (markers, etc)
echo "Downloading Leaflet images..."
curl -o lib/leaflet/images/marker-icon.png https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png
curl -o lib/leaflet/images/marker-shadow.png https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png
curl -o lib/leaflet/images/marker-icon-2x.png https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png
echo "✓ Leaflet images downloaded"

echo ""
echo "=== Vendorizing Complete ==="
echo "Libraries are now available in:"
echo "  - lib/d3/d3.v7.min.js"
echo "  - lib/leaflet/leaflet.min.js"
echo "  - lib/leaflet/leaflet.min.css"
echo "  - lib/leaflet/images/"
echo ""
echo "Next: Run 'git add lib/' and update HTML references in index.html"
