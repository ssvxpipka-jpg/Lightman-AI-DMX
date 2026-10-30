#!/bin/bash
# Build Lightman for macOS - creates DMG with PyInstaller + create-dmg
set -e

echo "=== Building Lightman for macOS ==="

# Step 1: Generate assets
echo "Step 1: Generating assets..."
python3 scripts/generate_assets.py

# Step 2: PyInstaller build
echo "Step 2: Building with PyInstaller..."
python3 -m PyInstaller \
  --noconfirm \
  --windowed \
  --onedir \
  --name "Lightman" \
  --icon "assets/icon.icns" \
  --add-data "shared:shared" \
  --add-data "config:config" \
  --add-data "fixtures_db:fixtures_db" \
  --add-data "assets:assets" \
  src/director/main.py

# Step 3: Create DMG (requires create-dmg to be installed)
echo "Step 3: Creating DMG..."

APP_NAME="Lightman"
DMG_NAME="Lightman.dmg"
DMG_DIR="dist/Lightman_dmg"
BACKGROUND="assets/dmg_background.png"

# Clean and create staging directory
rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"

# Copy app into staging
cp -R "dist/$APP_NAME.app" "$DMG_DIR/"

# Create symbolic link to Applications
ln -s /Applications "$DMG_DIR/Applications"

# Check if create-dmg is available
if command -v create-dmg &> /dev/null; then
  # Remove existing DMG if present
  rm -f "dist/$DMG_NAME"

  # Build DMG with background image
  create-dmg \
    --volname "$APP_NAME" \
    --window-pos 400 200 \
    --window-size 600 400 \
    --background "$BACKGROUND" \
    --icon-size 120 \
    --icon "$APP_NAME" 150 200 \
    --hide-extension "$APP_NAME" \
    --app-drop-link 450 200 \
    "dist/$DMG_NAME" \
    "$DMG_DIR"

  echo "✅ DMG created: dist/$DMG_NAME"
else
  echo "⚠️  create-dmg not installed. Install it with: brew install create-dmg"
  echo "⚠️  You can also manually create a DMG from: $DMG_DIR"
fi

echo ""
echo "=== Build complete ==="
echo "App bundle: dist/$APP_NAME.app"
echo "DMG: dist/$DMG_NAME"