"""
Lightman Server Client (STUB)
=============================
Future client for the Lightman Server OS (planned for v2.0).

Methods are empty stubs with documented return values.
"""

from __future__ import annotations

import logging
from typing import Optional

from shared.config import get_logger

logger = get_logger("server_client")


class ServerClient:
    """
    Stub client for connecting to a Lightman Server OS instance.
    Not implemented — coming in v2.0.
    """

    def __init__(self) -> None:
        self._connected: bool = False
        self._base_url: str = "http://localhost:11434"
        logger.info("ServerClient initialized (STUB — v2.0 feature)")

    def connect(self, login: str = "", password: str = "") -> bool:
        """
        Connect to the Lightman Server.

        Args:
            login: Server login username
            password: Server login password

        Returns:
            False — not implemented in current version.
        """
        # TODO: Implement server authentication and connection
        logger.warning("Server connect not implemented — v2.0 feature")
        self._connected = False
        return False

    def get_ollama_endpoint(self) -> str:
        """
        Return the Ollama API endpoint for local LLM inference.

        Returns:
            str: "http://localhost:11434"
        """
        return self._base_url

    def upload_backup(self, backup_path: str) -> bool:
        """
        Upload a backup file to the server.

        Args:
            backup_path: Path to the backup file

        Returns:
            False — not implemented in current version.
        """
        # TODO: Implement backup upload via server API
        logger.warning("Backup upload not implemented — v2.0 feature")
        return False

    def download_show(self, show_name: str) -> Optional[bytes]:
        """
        Download a show file from the server.

        Args:
            show_name: Name of the show to download

        Returns:
            None — not implemented in current version.
        """
        # TODO: Implement show file download
        logger.warning("Show download not implemented — v2.0 feature")
        return None

    def sync_fixtures(self) -> bool:
        """
        Synchronize fixture library with the server.

        Returns:
            False — not implemented in current version.
        """
        # TODO: Implement fixture library sync
        logger.warning("Fixture sync not implemented — v2.0 feature")
        return False

    @property
    def is_connected(self) -> bool:
        """Check if connected to the server."""
        return self._connected
