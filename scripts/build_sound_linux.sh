#!/usr/bin/env bash
# =============================================================================
# Lightman Sound — Linux build (PyInstaller + tar.gz bundle with .desktop)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
APP_NAME="LightmanSound"
APP_DIR="${DIST_DIR}/${APP_NAME}"
STAGE_DIR="${BUILD_DIR}/${APP_NAME}-stage"
ARCHIVE="${DIST_DIR}/${APP_NAME}-Linux.tar.gz"

cd "${PROJECT_ROOT}"

echo "==> [1/5] Checking tooling"
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
python3 -m pip show pyinstaller >/dev/null 2>&1 || \
    python3 -m pip install --upgrade pip pyinstaller

echo "==> [2/5] Installing audio dependencies (if missing)"
python3 -c "import sounddevice" >/dev/null 2>&1 || \
    python3 -m pip install --upgrade sounddevice librosa python-osc

echo "==> [3/5] Cleaning previous build"
rm -rf "${DIST_DIR}" "${BUILD_DIR}"

echo "==> [4/5] Running PyInstaller"
python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "${APP_NAME}" \
    --collect-all librosa \
    --collect-all sounddevice \
    --collect-all pythonosc \
    --add-data "${PROJECT_ROOT}/shared:shared" \
    --add-data "${PROJECT_ROOT}/src/director/theme.qss:src/director" \
    --add-data "${PROJECT_ROOT}/assets:assets" \
    src/sound/main.py

[ -d "${APP_DIR}" ] || { echo "!! PyInstaller output missing: ${APP_DIR}"; exit 1; }

echo "==> [5/5] Packaging tar.gz bundle"
mkdir -p "${STAGE_DIR}"
cp -r "${APP_DIR}/." "${STAGE_DIR}/"

# Launcher
cat > "${STAGE_DIR}/lightman-sound" << 'LAUNCH'
#!/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "${HERE}/LightmanSound" "$@"
LAUNCH
chmod +x "${STAGE_DIR}/lightman-sound"

# .desktop entry
cat > "${STAGE_DIR}/lightman-sound.desktop" << 'DESK'
[Desktop Entry]
Name=Lightman Sound
Comment=Audio capture and OSC bridge for Lightman
Exec=lightman-sound
Icon=lightman-sound
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
DESK

# Icon (optional)
if [ -f "${PROJECT_ROOT}/assets/icon.png" ]; then
    cp "${PROJECT_ROOT}/assets/icon.png" "${STAGE_DIR}/lightman-sound.png"
fi

# README
cat > "${STAGE_DIR}/README.txt" << 'README'
Lightman Sound — Linux bundle
------------------------------

Quick start:
  1. Extract this archive wherever you like.
  2. Run: ./lightman-sound

Desktop shortcut (optional):
  cp lightman-sound.desktop ~/.local/share/applications/
  cp lightman-sound          ~/.local/bin/   (or any dir in $PATH)

Audio loopback on Linux:
  Install PulseAudio/PipeWire loopback, or use:
    pactl load-module module-null-sink sink_name=LightmanLoop
  and set the app's input device accordingly.

Dependencies (if app fails to launch):
  libportaudio2, libsndfile1
    sudo apt install libportaudio2 libsndfile1
README

tar -C "${STAGE_DIR}" -czf "${ARCHIVE}" .

echo ""
echo "Done."
echo "  binary  -> ${APP_DIR}/${APP_NAME}"
echo "  archive -> ${ARCHIVE}"
echo ""
echo "Extract and run: tar -xzf ${ARCHIVE##*/} && ./lightman-sound"