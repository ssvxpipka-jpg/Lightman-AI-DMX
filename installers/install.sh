#!/bin/bash
# Lightman Installation Script (macOS / Linux)
# ==============================================
# Checks: Python 3.10+, creates venv, installs all dependencies.
# Handles PySide6 compatibility on macOS 12 (Python 3.14).

set -e

echo "========================================"
echo "  Lightman - Stage Lighting Automation  "
echo "  Installation Script (macOS / Linux)   "
echo "========================================"
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Darwin*)  PLATFORM="macOS" ;;
    Linux*)   PLATFORM="Linux" ;;
    *)        echo "Unsupported OS: $OS"; exit 1 ;;
esac
echo "Detected platform: $PLATFORM"

# Check Python
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "ERROR: Python 3 is not installed."
    exit 1
fi

# ─── Ollama Auto-Install ──────────────────────────────────────────────
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama is already installed."
fi
echo "Pulling Qwen model..."
ollama pull qwen2.5-coder:3b

# Check Python version (3.10+)
PY_VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PY_VERSION"
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo "ERROR: Python 3.10+ required. Found $PY_MAJOR.$PY_MINOR"
    exit 1
fi
echo "Python version OK (3.10+)"

# Create virtual environment (ensure on Python 3.12+)
VENV_DIR="venv"
if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 12 ]; then
    echo "Python 3.12+ detected - ensuring virtual environment..."
fi
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install PySide6 with version compatibility
echo ""
echo "Installing PySide6..."
if [ "$PLATFORM" = "macOS" ]; then
    # macOS 12 (Monterey) + Python 3.14: PySide6 6.10+ may not be available.
    # Try the known-compatible version 6.9.3 first.
    echo "  macOS detected - trying PySide6==6.9.3 first (macOS 12 compatibility)..."
    if pip install PySide6==6.9.3 2>/dev/null; then
        echo "  PySide6==6.9.3 installed successfully."
        echo "Installing remaining dependencies..."
        grep -v "^PySide6" requirements.txt > /tmp/lightman_req_no_pyside.txt
        pip install -r /tmp/lightman_req_no_pyside.txt
        rm -f /tmp/lightman_req_no_pyside.txt
    else
        echo "  PySide6==6.9.3 failed - trying latest compatible version..."
        pip install PySide6
        echo "Installing remaining dependencies..."
        grep -v "^PySide6" requirements.txt > /tmp/lightman_req_no_pyside.txt
        pip install -r /tmp/lightman_req_no_pyside.txt
        rm -f /tmp/lightman_req_no_pyside.txt
    fi
elif [ "$PLATFORM" = "Linux" ]; then
    echo "  Installing PySide6 (latest)..."
    pip install PySide6
    echo "Installing remaining dependencies..."
    grep -v "^PySide6" requirements.txt > /tmp/lightman_req_no_pyside.txt
    pip install -r /tmp/lightman_req_no_pyside.txt
    rm -f /tmp/lightman_req_no_pyside.txt
fi

# Check if PySide6 installed successfully
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo ""
    echo "========================================"
    echo "  WARNING: PySide6 failed to install!"
    echo "========================================"
    echo "PySide6 installation issue on this platform."
    echo "On macOS 12 with Python 3.14, please install"
    echo "Python 3.12 from python.org and re-run."
    echo "========================================"
fi

# Linux BLE notes
if [ "$PLATFORM" = "Linux" ]; then
    echo ""
    echo "NOTE: On Linux, BLE may require root privileges or bluetooth permissions."
    echo "      Run: sudo usermod -a -G bluetooth \$USER && reboot"
fi

echo ""
echo "========================================"
echo "  Installation completed successfully!  "
echo "========================================"
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Then run the Director:"
echo "  python -m src.director.main"

