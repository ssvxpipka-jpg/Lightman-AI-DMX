#!/bin/bash
set -e

echo "=== Lightman Linux Build ==="

# Step 1: Build with PyInstaller
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

# Step 2: Package into tar.gz
echo "Packaging output..."
mkdir -p dist
tar -czf "dist/Lightman-Linux.tar.gz" -C dist Lightman

# Step 3: Create desktop entry
echo "Creating desktop entry..."
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/lightman.desktop << DESKEOF
[Desktop Entry]
Name=Lightman
Comment=Stage Lighting Automation System
Exec=/usr/local/bin/lightman
Icon=/usr/local/bin/lightman
Type=Application
Categories=AudioVideo;Graphics;
DESKEOF

echo "=== Linux Build Complete ==="
