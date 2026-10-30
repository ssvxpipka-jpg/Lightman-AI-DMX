#!/bin/bash
set -e

echo "=== Lightman macOS Build ==="

# Step 1: Generate assets
echo "Generating assets..."
python3 scripts/generate_assets.py

# Step 2: Build with PyInstaller
echo "Building with PyInstaller..."
pyinstaller --noconfirm \
    --windowed \
    --onedir \
    --name "Lightman" \
    --icon "assets/app_icon.png" \
    --add-data "shared:shared" \
    --add-data "config:config" \
    --add-data "fixtures_db:fixtures_db" \
    --add-data "assets:assets" \
    src/director/main.py

# Step 3: Create DMG
echo "Creating DMG..."
create-dmg \
    --volname "Lightman Beta" \
    --window-pos 150 200 \
    --window-size 600 400 \
    --icon "dist/Lightman.app" 150 200 \
    --icon "Applications" 450 200 \
    --hide-extension "Lightman.app" \
    --app-drop-link 450 200 \
    dist/Lightman-Beta.dmg

echo "=== macOS Build Complete ==="
