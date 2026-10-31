#!/usr/bin/env bash
# =============================================================================
# Lightman — Linux .deb build.
# Downloads the GGUF model before PyInstaller so it's bundled.
# Ollama is NOT installed anymore.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
PKG_NAME="lightman"
PKG_VERSION="1.0.0"
PKG_ARCH="amd64"
PKG_ROOT="${BUILD_DIR}/deb-root"

MODEL_DIR="${PROJECT_ROOT}/assets/models"
MODEL_FILE="${MODEL_DIR}/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
HF_REPO="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF"
HF_FILE="qwen2.5-coder-3b-instruct-q4_k_m.gguf"

cd "${PROJECT_ROOT}"

echo "==> [1/6] Checking tooling"
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
command -v dpkg-deb >/dev/null || { echo "dpkg-deb required (apt install dpkg)"; exit 1; }
python3 -m pip show pyinstaller >/dev/null 2>&1 || python3 -m pip install pyinstaller
python3 -m pip show huggingface_hub >/dev/null 2>&1 || python3 -m pip install huggingface_hub

echo "==> [2/6] Ensuring GGUF model is downloaded"
mkdir -p "${MODEL_DIR}"
if [ ! -f "${MODEL_FILE}" ] || [ "$(stat -c%s "${MODEL_FILE}" 2>/dev/null || echo 0)" -lt 100000000 ]; then
    echo "    Downloading ${HF_FILE} (~2 GB, one-time)..."
    python3 - <<PY
import os
from huggingface_hub import hf_hub_download
os.makedirs("${MODEL_DIR}", exist_ok=True)
hf_hub_download(
    repo_id="${HF_REPO}",
    filename="${HF_FILE}",
    local_dir="${MODEL_DIR}",
)
import shutil, glob
target = "${MODEL_FILE}"
if not os.path.exists(target):
    for p in glob.glob(os.path.join("${MODEL_DIR}", "**", "${HF_FILE}"), recursive=True):
        if os.path.abspath(p) != os.path.abspath(target):
            shutil.copy2(p, target)
            break
print("Model present at:", target)
PY
else
    echo "    Model already present at ${MODEL_FILE}"
fi

echo "==> [3/6] Running PyInstaller"
rm -rf "${DIST_DIR}" "${BUILD_DIR}"
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name Lightman \
    --collect-all llama_cpp \
    --collect-all chromadb \
    --add-data "${PROJECT_ROOT}/assets:assets" \
    --add-data "${PROJECT_ROOT}/fixtures_db:fixtures_db" \
    --add-data "${PROJECT_ROOT}/src/director/theme.qss:src/director" \
    src/director/main.py

[ -d "${DIST_DIR}/Lightman" ] || { echo "!! PyInstaller output missing"; exit 1; }

echo "==> [4/6] Building deb tree"
rm -rf "${PKG_ROOT}"
mkdir -p "${PKG_ROOT}/DEBIAN"
mkdir -p "${PKG_ROOT}/opt/lightman"
mkdir -p "${PKG_ROOT}/usr/bin"
mkdir -p "${PKG_ROOT}/usr/share/applications"
mkdir -p "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps"

cp -r "${DIST_DIR}/Lightman/." "${PKG_ROOT}/opt/lightman/"

cat > "${PKG_ROOT}/usr/bin/lightman" << 'LAUNCH'
#!/bin/sh
exec /opt/lightman/Lightman "$@"
LAUNCH
chmod +x "${PKG_ROOT}/usr/bin/lightman"

cat > "${PKG_ROOT}/usr/share/applications/lightman.desktop" << 'DESK'
[Desktop Entry]
Name=Lightman
Comment=Lighting control studio with local AI
Exec=lightman
Icon=lightman
Terminal=false
Type=Application
Categories=AudioVideo;Graphics;
DESK

if [ -f "${PROJECT_ROOT}/assets/icon.png" ]; then
    cp "${PROJECT_ROOT}/assets/icon.png" \
       "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps/lightman.png"
fi

echo "==> [5/6] DEBIAN/control"
INSTALLED_SIZE=$(du -sk "${PKG_ROOT}" | cut -f1)
cat > "${PKG_ROOT}/DEBIAN/control" << CONTROL
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: graphics
Priority: optional
Architecture: ${PKG_ARCH}
Installed-Size: ${INSTALLED_SIZE}
Maintainer: Lightman <support@lightman.local>
Description: Lightman — lighting control studio with embedded AI
 PySide6-based lighting control app with an embedded llama-cpp-python
 LLM. No external Ollama or Python install is required at runtime.
CONTROL

cat > "${PKG_ROOT}/DEBIAN/postinst" << 'POSTINST'
#!/bin/sh
set -e
echo ""
echo "===================================================="
echo " Lightman installed. Launch with: lightman"
echo "===================================================="
exit 0
POSTINST
chmod 755 "${PKG_ROOT}/DEBIAN/postinst"

echo "==> [6/6] Building .deb"
dpkg-deb --build --root-owner-group "${PKG_ROOT}" \
    "${DIST_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"

echo ""
echo "Done."
echo "  .deb -> ${DIST_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
echo "  Install: sudo apt install ./${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"