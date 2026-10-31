"""
Universal console bridge.

Accepts "Titan", "Titan OS", "grandMA3 OS" etc. Port may be overridden
by the caller; otherwise uses the preset default.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_OK = True
except Exception:
    requests = None  # type: ignore
    REQUESTS_OK = False

try:
    from pythonosc.udp_client import SimpleUDPClient
    OSC_OK = True
except Exception:
    SimpleUDPClient = None  # type: ignore
    OSC_OK = False


CONSOLE_PRESETS = {
    "Titan":     {"protocol": "http", "port": 4430},
    "grandMA3":  {"protocol": "osc",  "port": 8000},
    "ChamSys":   {"protocol": "osc",  "port": 8000},
    "ETC Eos":   {"protocol": "osc",  "port": 8000},
    "QLC+":      {"protocol": "osc",  "port": 7700},
    "Mock":      {"protocol": "mock", "port": 0},
}


def _normalize_name(console: str) -> str:
    if not console:
        return "Mock"
    name = console.strip()
    if name.endswith(" OS"):
        name = name[:-3].strip()
    return name


class UniversalBridge:
    def __init__(
        self,
        console: str = "Mock",
        ip: str = "127.0.0.1",
        port: Optional[int] = None,
    ):
        self.console = _normalize_name(console)
        self.ip = ip or "127.0.0.1"

        preset = CONSOLE_PRESETS.get(
            self.console, {"protocol": "mock", "port": 0}
        )
        self.protocol = preset["protocol"]
        self.port = int(port) if port is not None else int(preset["port"])
        self._osc = None

        if self.protocol == "osc":
            if not OSC_OK:
                logger.error(
                    "python-osc not installed — cannot connect to %s",
                    self.console,
                )
                return
            try:
                self._osc = SimpleUDPClient(self.ip, self.port)
                logger.info(
                    "OSC bridge → %s @ %s:%d",
                    self.console, self.ip, self.port,
                )
            except Exception as e:
                logger.error("OSC init failed: %s", e)

        logger.info(
            "Bridge ready: console=%s protocol=%s %s:%d",
            self.console, self.protocol, self.ip, self.port,
        )

    def send_command(self, action: str, value: Any = 1) -> None:
        if self.protocol == "mock":
            print(f"[MOCK] {action} = {value}")
            return
        if self.protocol == "http":
            self._send_http(action, value)
            return
        if self.protocol == "osc":
            self._send_osc(action, value)
            return
        logger.warning("Unknown protocol: %s", self.protocol)

    def _send_http(self, action: str, value: Any) -> None:
        if not REQUESTS_OK:
            logger.error("requests not installed; cannot send HTTP")
            return
        endpoints = {
            "Blackout":    f"http://{self.ip}:{self.port}/titan/script/2/Playbacks/Blackout",
            "Strobe":      f"http://{self.ip}:{self.port}/titan/script/2/Playbacks/Flash",
            "Brightness+": f"http://{self.ip}:{self.port}/titan/script/2/Masters/Raise",
            "Brightness-": f"http://{self.ip}:{self.port}/titan/script/2/Masters/Lower",
            "Blue LED":    f"http://{self.ip}:{self.port}/titan/script/2/Colours/Blue",
            "Blue Fill":   f"http://{self.ip}:{self.port}/titan/script/2/Colours/FillBlue",
        }
        url = endpoints.get(
            action,
            f"http://{self.ip}:{self.port}/titan/script/2/{action.replace(' ', '')}",
        )
        try:
            r = requests.get(url, timeout=2)
            logger.info("HTTP %s → %s", action, r.status_code)
        except Exception as e:
            logger.error("HTTP send failed: %s", e)

    def _send_osc(self, action: str, value: Any) -> None:
        if not self._osc:
            logger.error("OSC client not available")
            return
        address = "/lightman/" + action.lower().replace(" ", "_")
        try:
            self._osc.send_message(address, value)
            logger.info("OSC %s = %s", address, value)
        except Exception as e:
            logger.error("OSC send failed: %s", e)