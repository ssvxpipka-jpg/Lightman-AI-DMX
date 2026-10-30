"""
Lightman Configuration and Path Management
===========================================
Cross-platform path configuration using pathlib.Path.
All sensitive data stored in hidden directories.
"""

from __future__ import annotations

import logging
import platform
from pathlib import Path
from typing import Optional


# ─── Platform Detection ──────────────────────────────────────────────

def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_linux() -> bool:
    return platform.system() == "Linux"


# ─── Base Paths ──────────────────────────────────────────────────────

# Project root (the Lightman directory)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Data directory for runtime data (git-ignored)
DATA_DIR: Path = PROJECT_ROOT / "data"

# Config directory
CONFIG_DIR: Path = PROJECT_ROOT / "config"

# Vendor directory (cloned repos, git-ignored)
VENDOR_DIR: Path = PROJECT_ROOT / "vendor"

# Fixtures database
FIXTURES_DB_DIR: Path = PROJECT_ROOT / "fixtures_db"
FIXTURES_DIR: Path = FIXTURES_DB_DIR  # alias for module imports

# Knowledge base
KNOWLEDGE_BASE_DIR: Path = PROJECT_ROOT / "knowledge_base"

# ─── Hidden / Secrets ───────────────────────────────────────────────

# Hidden secrets directory (.lightman_secrets/)
SECRETS_DIR: Path = PROJECT_ROOT / ".lightman_secrets"

# Local codes SQLite database
LOCAL_CODES_DB: Path = SECRETS_DIR / "local_codes.db"

# User database (SQLite)
USERS_DB: Path = DATA_DIR / "users.db"

# User profiles directory
PROFILES_DIR: Path = DATA_DIR / "profiles"

# ─── Home Directory Paths ───────────────────────────────────────────

# Logs directory in user home (cross-platform)
LOGS_DIR: Path = Path.home() / ".lightman" / "logs"

LOG_FILE: Path = LOGS_DIR / "lightman.log"


# ─── Directory Initialization ────────────────────────────────────────

def ensure_directories() -> None:
    """Create all runtime directories if they don't exist."""
    for d in [
        DATA_DIR,
        DATA_DIR / "profiles",
        CONFIG_DIR,
        SECRETS_DIR,
        LOGS_DIR,
        FIXTURES_DB_DIR,
        KNOWLEDGE_BASE_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


# ─── Logging Setup ───────────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging to both file and console.
    Log file goes to ~/.lightman/logs/lightman.log
    """
    ensure_directories()

    logger = logging.getLogger("lightman")
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler (cross-platform, in home directory)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "[%(levelname)s] %(message)s",
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Lightman initialized on {platform.system()}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Project root: {PROJECT_ROOT}")

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger that inherits Lightman's configuration."""
    if name:
        logger = logging.getLogger(f"lightman.{name}")
    else:
        logger = logging.getLogger("lightman")
    if not logging.getLogger("lightman").handlers:
        setup_logging()
    return logger
