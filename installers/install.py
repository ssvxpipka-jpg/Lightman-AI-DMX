#!/usr/bin/env python3
"""
Lightman Cross-Platform Installation Script
============================================
Handles installation on macOS, Windows, and Linux.
Run: python installers/install.py

Checks:
  - Python 3.10+
  - Creates venv (ensured on Python 3.12+)
  - Installs all requirements with PySide6 compatibility
    (PySide6==6.9.3 on macOS 12, latest PySide6 on other platforms)
"""

from __future__ import annotations

import os
import sys
import subprocess
import platform
import shutil

# ─── Platform Detection ──────────────────────────────────────────────

def detect_platform() -> str:
    """Detect the current operating system."""
    system = platform.system()
    if system == "Darwin":
        return "macOS"
    elif system == "Windows":
        return "Windows"
    elif system == "Linux":
        return "Linux"
    else:
        return "Unknown"


def check_python_version() -> bool:
    """Verify Python 3.10+ is running."""
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        print(f"ERROR: Python 3.10+ required. Found {major}.{minor}.")
        return False
    print(f"Python {major}.{minor}.{sys.version_info[2]} OK")
    return True


# ─── Ollama Auto-Install ──────────────────────────────────────────────

def install_ollama() -> None:
    """Install Ollama (if missing) and pull the Qwen model."""
    print("Checking Ollama...")
    if not shutil.which("ollama"):
        print("Ollama not found. Installing...")
        if platform.system() == "Windows":
            subprocess.run(
                ["winget", "install", "Ollama.Ollama",
                 "--accept-source-agreements", "--accept-package-agreements"]
            )
        else:
            subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh",
                shell=True,
            )
    print("Pulling Qwen model...")
    subprocess.run(["ollama", "pull", "qwen2.5-coder:3b"])
    print("Ollama + Qwen model ready.")


# ─── Virtual Environment ─────────────────────────────────────────────

def create_venv(platform_name: str) -> str:
    """Create a virtual environment and return its bin/Scripts path."""
    venv_dir = "venv"
    if platform_name == "Windows":
        python_exe = sys.executable
        venv_path = os.path.join(venv_dir, "Scripts")
    else:
        python_exe = sys.executable
        venv_path = os.path.join(venv_dir, "bin")

    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 12):
        print(f"Python {major}.{minor} detected - ensuring virtual environment...")

    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment at {venv_dir}/...")
        subprocess.run([python_exe, "-m", "venv", venv_dir], check=True)

    return venv_path


def pip_install(venv_path: str, platform_name: str) -> None:
    """Install dependencies from requirements.txt with PySide6 compatibility."""
    if platform_name == "Windows":
        pip_exe = os.path.join(venv_path, "pip.exe")
    else:
        pip_exe = os.path.join(venv_path, "pip")

    print("Upgrading pip...")
    subprocess.run([pip_exe, "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)

    # Read requirements to separate PySide6 from the rest
    req_file = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    req_file = os.path.abspath(req_file)
    with open(req_file) as f:
        all_reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    other_reqs = [r for r in all_reqs if not r.startswith("PySide6")]

    # Write a temp requirements file excluding PySide6
    import tempfile
    tmp_req = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="lightman_reqs_")
    for req in other_reqs:
        tmp_req.write(req + "\n")
    tmp_req.close()

    print("Installing PySide6...")
    if platform_name == "macOS":
        # macOS 12 (Monterey) + Python 3.14: PySide6 6.10+ may not be available.
        # Try the known-compatible version 6.9.3 first.
        print("  macOS detected - trying PySide6==6.9.3 first (macOS 12 compatibility)...")
        result = subprocess.run([pip_exe, "install", "PySide6==6.9.3"], capture_output=True)
        if result.returncode == 0:
            print("  PySide6==6.9.3 installed successfully.")
        else:
            print("  PySide6==6.9.3 failed - trying latest compatible version...")
            subprocess.run([pip_exe, "install", "PySide6"], check=True)
    else:
        subprocess.run([pip_exe, "install", "PySide6"], check=True)

    print("Installing remaining dependencies...")
    subprocess.run([pip_exe, "install", "-r", tmp_req.name], check=True)
    os.unlink(tmp_req.name)

    # Linux BLE notes
    if platform_name == "Linux":
        print("NOTE: On Linux, BLE may require root privileges or bluetooth permissions.")
        print("      Run: sudo usermod -a -G bluetooth $USER && reboot")

    # Check if PySide6 installed successfully
    check_cmd = [pip_exe, "show", "PySide6"]
    result = subprocess.run(check_cmd, capture_output=True)
    if result.returncode != 0:
        print("\n" + "=" * 40)
        print("  WARNING: PySide6 failed to install!")
        print("=" * 40)
        if platform_name == "macOS":
            print("On macOS 12 with Python 3.14, please install")
            print("Python 3.12 from python.org and re-run.")
        else:
            print("Please check https://pyside.org for compatibility info.")
        print("=" * 40)


# ─── Post-Install ────────────────────────────────────────────────────

def post_install_instructions(platform_name: str) -> None:
    """Print instructions for the user after installation."""
    print("\n" + "=" * 40)
    print("  Installation completed successfully!")
    print("=" * 40 + "\n")
    if platform_name == "Windows":
        print("To activate the environment, run:")
        print("  venv\\Scripts\\activate.bat")
    else:
        print("To activate the environment, run:")
        print("  source venv/bin/activate")
    print("\nThen run the Director:")
    print("  python -m src.director.main")


# ─── Main ────────────────────────────────────────────────────────────

def main() -> None:
    if not check_python_version():
        sys.exit(1)

    platform_name = detect_platform()
    print(f"Detected platform: {platform_name}")

    venv_path = create_venv(platform_name)
    pip_install(venv_path, platform_name)
    install_ollama()
    post_install_instructions(platform_name)


if __name__ == "__main__":
    main()

