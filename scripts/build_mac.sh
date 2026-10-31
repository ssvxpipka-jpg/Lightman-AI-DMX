#!/usr/bin/env bash
# =============================================================================
# Lightman — macOS build (PyInstaller .app + .dmg).
# Downloads the GGUF model into assets/models BEFORE PyInstaller so the model
# is bundled inside the .app. Ollama is NOT installed anymore.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
APP_NAME="Lightman"
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
DMG_PATH="${DIST_DIR}/${APP_NAME}.dmg"

MODEL_DIR="${PROJECT_ROOT}/assets/models"
MODEL_FILE="${MODEL_DIR}/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
HF_REPO="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF"
HF_FILE="qwen2.5-coder-3b-instruct-q4_k_m.gguf"

cd "${PROJECT_ROOT}"

echo "==> [1/5] Tooling check"
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
python3 -m pip show pyinstaller >/dev/null 2>&1 || \
    python3 -m pip install --upgrade pip pyinstaller
python3 -m pip show huggingface_hub >/dev/null 2>&1 || \
    python3 -m pip install --upgrade huggingface_hub

if command -v create-dmg >/dev/null 2>&1; then
    USE_CREATE_DMG=1
else
    echo "!! create-dmg not found — using hdiutil"
    USE_CREATE_DMG=0
fi

echo "==> [2/5] Ensuring GGUF model is downloaded"
mkdir -p "${MODEL_DIR}"
if [ ! -f "${MODEL_FILE}" ] || [ "$(stat -f%z "${MODEL_FILE}" 2>/dev/null || echo 0)" -lt 100000000 ]; then
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
# Some snapshots nest by subdir; normalize to flat path.
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

echo "==> [3/5] PyInstaller"
rm -rf "${DIST_DIR}" "${BUILD_DIR}"
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "${APP_NAME}" \
    --collect-all llama_cpp \
    --collect-all chromadb \
    --add-data "${PROJECT_ROOT}/assets:assets" \
    --add-data "${PROJECT_ROOT}/fixtures_db:fixtures_db" \
    --add-data "${PROJECT_ROOT}/src/director/theme.qss:src/director" \
    src/director/main.py

[ -d "${APP_BUNDLE}" ] || { echo "!! .app not built"; exit 1; }

echo "==> [4/5] Building DMG"
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
    hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_BUNDLE}" \
        -ov -format UDZO "${DMG_PATH}"
fi

echo "==> [5/5] Done"
echo "    .app -> ${APP_BUNDLE}"
echo "    .dmg -> ${DMG_PATH}"