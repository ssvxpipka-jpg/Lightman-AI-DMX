import asyncio
import logging
import threading
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    from bless import (
        BlessServer,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
        GATTAttributePermissions,
    )
    BLESS_AVAILABLE = True
except Exception as e:
    BlessServer = None
    BlessGATTCharacteristic = None
    GATTCharacteristicProperties = None
    GATTAttributePermissions = None
    BLESS_AVAILABLE = False
    logger.warning("bless library not available: %s", e)

try:
    from bleak import BleakScanner
    BLEAK_AVAILABLE = True
except Exception as e:
    BleakScanner = None
    BLEAK_AVAILABLE = False
    logger.warning("bleak library not available: %s", e)


SERVICE_UUID = "0000ffff-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"


class BLEAdvertiser:
    """Advertise the Lightman pairing code over BLE using `bless`."""

    def __init__(self, code: str):
        self.code = str(code)
        self.name = f"Lightman-{self.code}"
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server: Any = None
        self._stop_event: asyncio.Event | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name=f"BLEAdvertiser-{self.code}",
        )
        self._thread.start()

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run_server())
        except Exception as e:
            logger.error("BLE advertiser loop error: %s", e, exc_info=True)
        finally:
            try:
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self._loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:
                pass
            try:
                self._loop.close()
            except Exception:
                pass

    async def _run_server(self) -> None:
        if not BLESS_AVAILABLE:
            logger.error("bless is not installed; cannot advertise.")
            return

        self._stop_event = asyncio.Event()

        try:
            self._server = BlessServer(name=self.name, loop=self._loop)
            self._server.read_request_func = self._on_read
            self._server.write_request_func = self._on_write

            await self._server.add_new_service(SERVICE_UUID)
            await self._server.add_new_characteristic(
                SERVICE_UUID,
                CHARACTERISTIC_UUID,
                GATTCharacteristicProperties.read
                | GATTCharacteristicProperties.write,
                bytearray(self.code.encode("utf-8")),
                GATTAttributePermissions.readable
                | GATTAttributePermissions.writeable,
            )
            await self._server.start()
            logger.info("Advertising as %s", self.name)

            await self._stop_event.wait()

            try:
                await self._server.stop()
            except Exception as e:
                logger.error("Error stopping BLE server: %s", e)
        except Exception as e:
            logger.error("BLE advertising failed: %s", e, exc_info=True)

    def _on_read(self, characteristic: Any, **kwargs: Any) -> bytearray:
        return bytearray(self.code.encode("utf-8"))

    def _on_write(self, characteristic: Any, value: bytearray, **kwargs: Any) -> None:
        try:
            logger.info("BLE write received: %s", bytes(value))
        except Exception:
            logger.info("BLE write received (unprintable).")

    def stop(self) -> None:
        if self._loop is not None and self._stop_event is not None:
            try:
                if not self._loop.is_closed():
                    self._loop.call_soon_threadsafe(self._stop_event.set)
            except Exception as e:
                logger.error("Error requesting BLE stop: %s", e)

        if self._thread is not None:
            self._thread.join(timeout=3.0)


async def scan_for_lightman(timeout: float = 5.0) -> List[Dict[str, Any]]:
    if not BLEAK_AVAILABLE:
        logger.error("bleak is not installed; cannot scan.")
        return []

    results: List[Dict[str, Any]] = []
    try:
        devices = await BleakScanner.discover(timeout=timeout)
        for device in devices:
            name = getattr(device, "name", None) or ""
            if "Lightman" in name:
                results.append(
                    {
                        "name": name,
                        "address": getattr(device, "address", ""),
                        "rssi": getattr(device, "rssi", None),
                    }
                )
    except Exception as e:
        logger.error("BLE scan failed: %s", e, exc_info=True)

    return results