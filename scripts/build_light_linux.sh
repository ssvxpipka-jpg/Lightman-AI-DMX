#!/usr/bin/env bash
# =============================================================================
# Lightman Light — Linux build (PyInstaller + tar.gz bundle with .desktop)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
APP_NAME="LightmanLight"
APP_DIR="${DIST_DIR}/${APP_NAME}"
STAGE_DIR="${BUILD_DIR}/${APP_NAME}-stage"
ARCHIVE="${DIST_DIR}/${APP_NAME}-Linux.tar.gz"

cd "${PROJECT_ROOT}"

echo "==> [1/5] Checking tooling"
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
python3 -m pip show pyinstaller >/dev/null 2>&1 || \
    python3 -m pip install --upgrade pip pyinstaller

echo "==> [2/5] Installing console bridge dependencies (if missing)"
python3 -c "import pythonosc" >/dev/null 2>&1 || \
    python3 -m pip install --upgrade python-osc requests

echo "==> [3/5] Cleaning previous build"
rm -rf "${DIST_DIR}" "${BUILD_DIR}"

echo "==> [4/5] Running PyInstaller"
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "${APP_NAME}" \
    --collect-all pythonosc \
    --collect-all requests \
    --add-data "${PROJECT_ROOT}/shared:shared" \
    --add-data "${PROJECT_ROOT}/src/director/theme.qss:src/director" \
    --add-data "${PROJECT_ROOT}/assets:assets" \
    src/light/main.py

[ -d "${APP_DIR}" ] || { echo "!! PyInstaller output missing: ${APP_DIR}"; exit 1; }

echo "==> [5/5] Packaging tar.gz bundle"
mkdir -p "${STAGE_DIR}"
cp -r "${APP_DIR}/." "${STAGE_DIR}/"

# Launcher
cat > "${STAGE_DIR}/lightman-light" << 'LAUNCH'
#!/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "${HERE}/LightmanLight" "$@"
LAUNCH
chmod +x "${STAGE_DIR}/lightman-light"

# .desktop entry
cat > "${STAGE_DIR}/lightman-light.desktop" << 'DESK'
[Desktop Entry]
Name=Lightman Light
Comment=Console bridge for Lightman (Titan, grandMA3, ChamSys, ETC Eos, QLC+)
Exec=lightman-light
Icon=lightman-light
Terminal=false
Type=Application
Categories=AudioVideo;Graphics;
DESK

# Icon (optional)
if [ -f "${PROJECT_ROOT}/assets/icon.png" ]; then
    cp "${PROJECT_ROOT}/assets/icon.png" "${STAGE_DIR}/lightman-light.png"
fi

# README
cat > "${STAGE_DIR}/README.txt" << 'README'
Lightman Light — Linux bundle
------------------------------

Quick start:
  1. Extract this archive wherever you like.
  2. Run: ./lightman-light

Desktop shortcut (optional):
  cp lightman-light.desktop ~/.local/share/applications/
  cp lightman-light          ~/.local/bin/   (or any dir in $PATH)

Supported consoles:
  Titan       — HTTP on port 4430
  grandMA3    — OSC  on port 8000
  ChamSys     — OSC  on port 9000
  ETC Eos     — OSC  on port 8000
  QLC+        — OSC  on port 7700
  Mock        — prints commands to stdout

The "Test Commands" group is visible only when "Mock" is selected.
README

tar -C "${STAGE_DIR}" -czf "${ARCHIVE}" .

echo ""
echo "Done."
echo "  binary  -> ${APP_DIR}/${APP_NAME}"
echo "  archive -> ${ARCHIVE}"
echo ""
echo "Extract and run: tar -xzf ${ARCHIVE##*/} && ./lightman-light"