#!/bin/bash
# Применить новую главную к dist (после npm run build + postbuild.py)
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"
cp "$R/homepage-static/index.html" "$R/dist/index.html"
cp "$R/homepage-static/support.js" "$R/dist/support.js"
cp "$R/homepage-static/img/licenses/lic1.webp" "$R/dist/img/licenses/"
cp "$R/homepage-static/img/gallery/hall.webp" "$R/dist/img/gallery/"
cp "$R/homepage-static/img/logo.svg" "$R/homepage-static/img/logo-white.svg" "$R/dist/img/"
echo "homepage applied to dist/"
