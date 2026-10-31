#!/usr/bin/env bash
# =============================================================================
# Lightman Light — macOS build script (PyInstaller .app + .dmg)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
APP_NAME="LightmanLight"
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
DMG_PATH="${DIST_DIR}/${APP_NAME}.dmg"

cd "${PROJECT_ROOT}"

echo "==> [1/4] Checking tooling"
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
python3 -m pip show pyinstaller >/dev/null 2>&1 || \
    python3 -m pip install --upgrade pip pyinstaller

if command -v create-dmg >/dev/null 2>&1; then
    USE_CREATE_DMG=1
else
    echo "!! create-dmg not found — using hdiutil (brew install create-dmg for nicer DMG)"
    USE_CREATE_DMG=0
fi

echo "==> [2/4] Cleaning previous build"
rm -rf "${DIST_DIR}" "${BUILD_DIR}"

echo "==> [3/4] Running PyInstaller"
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "${APP_NAME}" \
    --collect-all pythonosc \
    --collect-all requests \
    --add-data "${PROJECT_ROOT}/assets:assets" \
    --add-data "${PROJECT_ROOT}/src/director/theme.qss:src/director" \
    src/light/main.py

[ -d "${APP_BUNDLE}" ] || { echo "!! .app not built"; exit 1; }

echo "==> [4/4] Building DMG"
rm -f "${DMG_PATH}"
if [ "${USE_CREATE_DMG}" -eq 1 ]; then
    create-dmg \
        --volname "${APP_NAME}" \
        --window-pos 200 120 \
        --window-size 800 480 \
        --icon-size 96 \
        --icon "${APP_NAME}.app" 200 200 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 600 200 \
        "${DMG_PATH}" \
        "${APP_BUNDLE}"
else
    hdiutil create -volname "${APP_NAME}" \
        -srcfolder "${APP_BUNDLE}" -ov -format UDZO "${DMG_PATH}"
fi

echo ""
echo "Done."
echo "  .app -> ${APP_BUNDLE}"
echo "  .dmg -> ${DMG_PATH}"