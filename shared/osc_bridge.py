"""
OSC client wrapper for Lightman Sound → Director communication.

Public API:
    OSCClient(ip, port)
    .send_bpm(bpm: float)
    .send_beat(index: int)
    .send_energy(energy: float)
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from pythonosc.udp_client import SimpleUDPClient
    OSC_OK = True
except Exception as _e:  # pragma: no cover
    SimpleUDPClient = None  # type: ignore
    OSC_OK = False
    logger.warning("pythonosc unavailable: %s", _e)


class OSCClient:
    """Thin UDP OSC client. Silently no-ops when pythonosc is missing."""

    def __init__(self, ip: str = "127.0.0.1", port: int = 8000):
        self.ip = ip
        self.port = int(port)
        self._client = None

        if OSC_OK:
            try:
                self._client = SimpleUDPClient(self.ip, self.port)
                logger.info("OSC client → %s:%d", self.ip, self.port)
            except Exception as e:
                logger.error("OSC client init failed: %s", e)

    def _send(self, address: str, value: Any) -> None:
        if not self._client:
            logger.warning("OSC unavailable; skip %s=%s", address, value)
            return
        try:
            self._client.send_message(address, value)
        except Exception as e:
            logger.error("OSC send failed (%s=%s): %s", address, value, e)

    def send_bpm(self, bpm: float) -> None:
        self._send("/lightman/bpm", float(bpm))

    def send_beat(self, index: int = 1) -> None:
        self._send("/lightman/beat", int(index))

    def send_energy(self, energy: float) -> None:
        self._send("/lightman/energy", float(energy))