#!/usr/bin/env python3
"""
Lightman Console Manager
========================
Plugin-style adapter system for lighting console protocols.

Supported consoles:
  - Titan WebAPI     (Avolites) — HTTP REST, port 4430
  - grandMA3 OSC     (MA Lighting) — OSC/TCP, port 8000
  - grandMA2 Telnet  (MA Lighting) — Telnet/TCP, port 3000
  - MagicQ UDP       (ChamSys) — UDP, port 6553
  - Eos OSC          (ETC) — OSC/TCP, port 3037
  - QLC+ OSC         (QLC+) — OSC/UDP, port 9938

Usage:
    from shared.console_manager import ConsoleManager
    mgr = ConsoleManager()
    console = mgr.create_adapter("titan-webapi", ip="192.168.1.10")
"""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Optional

from shared.config import get_logger, FIXTURES_DIR

logger = get_logger("console_manager")

CONSOLES_PATH = FIXTURES_DIR / "consoles_catalog.json"


class BaseConsoleAdapter:
    """Base class for console protocol adapters."""

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self._connected = False

    def connect(self) -> bool:
        """Open a connection to the console. Return True on success."""
        try:
            with socket.create_connection((self.ip, self.port), timeout=2.0):
                self._connected = True
                logger.info(f"Connected to console at {self.ip}:{self.port}")
                return True
        except Exception as e:
            logger.error(f"Connection failed to {self.ip}:{self.port}: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Close the connection."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def patch_fixture(self, fixture_id: str, start_address: int) -> None:
        """Patch a fixture to a DMX start address. Stub."""
        logger.debug(f"patch_fixture({fixture_id}, {start_address}) - stub")

    def set_level(self, channel: int, value: float) -> None:
        """Set a DMX channel level (0.0-1.0). Stub."""
        logger.debug(f"set_level({channel}, {value}) - stub")

    def trigger_playback(self, playback_id: int) -> None:
        """Trigger a playback or cue. Stub."""
        logger.debug(f"trigger_playback({playback_id}) - stub")


class TitanAdapter(BaseConsoleAdapter):
    """Avolites Titan WebAPI — HTTP REST on port 4430."""

    def __init__(self, ip: str = "127.0.0.1"):
        super().__init__(ip, 4430)

    def connect(self) -> bool:
        """Test HTTP REST connection to Titan WebAPI."""
        import urllib.request
        try:
            url = f"http://{self.ip}:{self.port}/titan/get/System/SoftwareVersion"
            urllib.request.urlopen(url, timeout=3)
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Titan connection failed: {e}")
            self._connected = False
            return False

    def fire_cue(self, cue_number: int) -> bool:
        """Fire a playback via HTTP REST API."""
        import urllib.request
        if not self._connected:
            return False
        url = (f"http://{self.ip}:{self.port}/titan/script/Playbacks/"
               f"SelectPlaybackAtLevel?int={cue_number}&float=1.0&bool=false")
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except Exception as e:
            logger.error(f"Titan fire_cue failed: {e}")
            return False


class GrandMA3Adapter(BaseConsoleAdapter):
    """grandMA3 OSC over TCP on port 8000."""

    def __init__(self, ip: str = "127.0.0.1"):
        super().__init__(ip, 8000)


class GrandMA2Adapter(BaseConsoleAdapter):
    """grandMA2 Telnet on port 3000."""

    def __init__(self, ip: str = "127.0.0.1"):
        super().__init__(ip, 3000)


class ChamSysAdapter(BaseConsoleAdapter):
    """ChamSys MagicQ UDP on port 6553."""

    def __init__(self, ip: str = "127.0.0.1"):
        super().__init__(ip, 6553)

    def connect(self) -> bool:
        """Open UDP socket (connectionless, just bind)."""
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.settimeout(2.0)
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"MagicQ connection failed: {e}")
            self._connected = False
            return False

    _sock = None  # will be set in connect()


class EosAdapter(BaseConsoleAdapter):
    """ETC Eos OSC over TCP on port 3037."""

    def __init__(self, ip: str = "127.0.0.1"):
        super().__init__(ip, 3037)


class QLCPlusAdapter(BaseConsoleAdapter):
    """QLC+ OSC on port 9938, Web API on port 9005."""

    def __init__(self, ip: str = "127.0.0.1"):
        super().__init__(ip, 9938)
        self.web_port = 9005


class HogAdapter(BaseConsoleAdapter):
    """Highland Hog OS OSC on port 6900."""

    def __init__(self, ip: str = "127.0.0.1"):
        super().__init__(ip, 6900)


# ─── Console Manager ─────────────────────────────────────────────────

_ADAPTER_REGISTRY = {
    "TitanAdapter": TitanAdapter,
    "GrandMA3Adapter": GrandMA3Adapter,
    "GrandMA2Adapter": GrandMA2Adapter,
    "ChamSysAdapter": ChamSysAdapter,
    "EosAdapter": EosAdapter,
    "QLCPlusAdapter": QLCPlusAdapter,
    "HogAdapter": HogAdapter,
}

# Legacy catalog names → adapter class names
_CONSOLE_ID_MAP = {
    "titan-webapi": "TitanAdapter",
    "gma3-osc": "GrandMA3Adapter",
    "gma2-telnet": "GrandMA2Adapter",
    "magicq-udp": "ChamSysAdapter",
    "eos-osc": "EosAdapter",
    "qlc-osc": "QLCPlusAdapter",
    "qlc-web": "QLCPlusAdapter",
    "hog-osc": "HogAdapter",
}


class ConsoleManager:
    """Manage console adapters and their catalog definitions."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or CONSOLES_PATH
        self._catalog: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self._active_adapters: dict[str, BaseConsoleAdapter] = {}
        self._load()

    def _load(self):
        """Load the console catalog from JSON."""
        try:
            with open(self.catalog_path, "r") as f:
                self._catalog = json.load(f)
            self._by_id = {c["id"]: c for c in self._catalog}
            logger.info(f"Loaded {len(self._catalog)} console profiles")
        except FileNotFoundError:
            logger.warning(f"Console catalog not found: {self.catalog_path}")
            self._catalog = []
            self._by_id = {}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading console catalog: {e}")
            self._catalog = []
            self._by_id = {}

    @property
    def all(self) -> list[dict]:
        return self._catalog

    def get(self, console_id: str) -> Optional[dict]:
        """Look up a console profile by ID."""
        return self._by_id.get(console_id)

    def search(self, query: str) -> list[dict]:
        """Search consoles by name, manufacturer, or protocol."""
        q = query.lower().strip()
        return [c for c in self._catalog
                if q in c.get("name", "").lower()
                or q in c.get("manufacturer", "").lower()
                or q in c.get("protocol", "").lower()]

    def create_adapter(self, console_id: str, ip: str = "127.0.0.1") -> Optional[BaseConsoleAdapter]:
        """Create an adapter instance for the given console ID."""
        # Try catalog first
        profile = self._by_id.get(console_id)
        if profile:
            adapter_cls_name = profile.get("adapter_class") or _CONSOLE_ID_MAP.get(console_id)
        else:
            adapter_cls_name = _CONSOLE_ID_MAP.get(console_id)

        adapter_cls = _ADAPTER_REGISTRY.get(adapter_cls_name)
        if not adapter_cls:
            logger.error(f"Unknown console ID: {console_id}")
            return None

        # Get port from catalog or use adapter default
        port = None
        if profile:
            port = profile.get("default_port")

        if port:
            adapter = adapter_cls(ip=ip, port=port)
        else:
            adapter = adapter_cls(ip=ip)

        self._active_adapters[console_id] = adapter
        return adapter

    def get_adapter(self, console_id: str) -> Optional[BaseConsoleAdapter]:
        """Retrieve a previously created adapter, or create one."""
        if console_id in self._active_adapters:
            return self._active_adapters[console_id]
        return self.create_adapter(console_id)

    def test_all(self) -> dict:
        """Test connection to all registered consoles."""
        results = {}
        for console_id in self._by_id:
            adapter = self.create_adapter(console_id)
            if adapter:
                results[console_id] = adapter.connect()
            else:
                results[console_id] = False
        return results
