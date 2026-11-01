"""Shared logging setup for Lightman."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

_LOG_DIR = Path("data/logs")


def setup_logger(debug_enabled: bool = False) -> None:
    """Initialise logging.

    If *debug_enabled* is True, debug logs are written to
    ``data/logs/lightman_YYYYMMDD_HHMMSS.log``.  Otherwise only console
    output at ERROR level is active.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug_enabled else logging.ERROR)

    # Remove all existing handlers so we can reconfigure cleanly.
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Console handler.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug_enabled else logging.ERROR)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    if debug_enabled:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = _LOG_DIR / f"lightman_{timestamp}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def toggle_debug(enabled: bool) -> None:
    """Change debug mode on the fly."""
    setup_logger(enabled)
