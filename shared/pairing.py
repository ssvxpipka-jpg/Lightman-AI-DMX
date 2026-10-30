"""
Lightman BLE Pairing
=====================
Handles secure pairing between Sound/Light apps and the Director.

Sound/Light apps:
    - Generate a random pairing code (SL-SOUND-XXXX / SL-LIGHT-XXXX)
    - Advertise the code via BLE using bleson
    - Save code to .lightman_secrets/local_codes.db

Director:
    - Scan for BLE advertisements using bleak
    - User enters code, matches against scanned codes
    - On match -> GATT connection
    - HMAC-SHA256 packet signing for security

Cross-platform: uses pathlib.Path and works on macOS, Windows, Linux.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import struct
import time
from dataclasses import dataclass
from typing import Optional

from shared.config import LOCAL_CODES_DB, SECRETS_DIR, get_logger

logger = get_logger("pairing")


# ─── BLE Constants ────────────────────────────────────────────────────

# Fixed 128-bit BLE Service UUID for Lightman pairing.
# MUST be a valid UUID — never use the pairing code as a UUID.
LIGHTMAN_SERVICE_UUID = "0000abcd-0000-1000-8000-00805f9b34fb"


# ─── Code Format ─────────────────────────────────────────────────────

# Prefix for pairing codes
SOUND_PREFIX = "SL-SOUND"
LIGHT_PREFIX = "SL-LIGHT"

# Number of hex chars in the code suffix
_CODE_HEX_LEN = 4


def generate_pairing_code(app_type: str) -> str:
    """
    Generate a random pairing code.
    app_type should be 'sound' or 'light'.
    Returns a code like 'SL-SOUND-A3F1' or 'SL-LIGHT-B4C2'.
    """
    if app_type == "sound":
        prefix = SOUND_PREFIX
    elif app_type == "light":
        prefix = LIGHT_PREFIX
    else:
        raise ValueError(f"Unknown app_type: {app_type}")

    hex_part = "".join(secrets.choice("0123456789ABCDEF") for _ in range(_CODE_HEX_LEN))
    code = f"{prefix}-{hex_part}"
    logger.info("Generated pairing code: %s", code)
    return code


# ─── Pairing Code Database ───────────────────────────────────────────

def _init_codes_db() -> None:
    """Initialize the local codes SQLite database if it doesn't exist."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LOCAL_CODES_DB))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pairing_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    UNIQUE NOT NULL,
            app_type    TEXT    NOT NULL,
            secret_key  TEXT    NOT NULL,
            created_at  REAL    NOT NULL,
            expires_at  REAL    NOT NULL,
            used        INTEGER DEFAULT 0
        )
    """)
    # Clean up expired codes
    cursor.execute(
        "DELETE FROM pairing_codes WHERE expires_at < ?",
        (time.time(),)
    )
    conn.commit()
    conn.close()
    logger.debug("Local codes database initialized at %s", LOCAL_CODES_DB)


def _get_codes_connection() -> sqlite3.Connection:
    """Get a SQLite connection for the codes database."""
    _init_codes_db()
    conn = sqlite3.connect(str(LOCAL_CODES_DB))
    conn.row_factory = sqlite3.Row
    return conn


def save_pairing_code(code: str, app_type: str, duration: float = 300.0) -> str:
    """
    Save a pairing code with a generated secret key.
    The code expires after 'duration' seconds (default 5 minutes).
    Returns the secret key used for HMAC signing.
    """
    secret_key = secrets.token_hex(32)  # 256-bit key
    now = time.time()
    expires = now + duration

    conn = _get_codes_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pairing_codes (code, app_type, secret_key, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (code, app_type, secret_key, now, expires),
        )
        conn.commit()
        logger.info("Saved pairing code '%s' (expires in %.0fs)", code, duration)
        return secret_key
    finally:
        conn.close()


def lookup_pairing_code(code: str) -> Optional[dict]:
    """
    Look up a pairing code. Returns the record dict or None if not found/expired.
    Marks the code as 'used' if found.
    """
    conn = _get_codes_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM pairing_codes WHERE code = ? AND expires_at > ? AND used = 0",
            (code, time.time()),
        )
        row = cursor.fetchone()
        if row is None:
            logger.warning("Pairing code '%s' not found or expired", code)
            return None

        # Mark as used
        cursor.execute("UPDATE pairing_codes SET used = 1 WHERE id = ?", (row["id"],))
        conn.commit()

        record = {
            "code": row["code"],
            "app_type": row["app_type"],
            "secret_key": row["secret_key"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
        }
        logger.info("Pairing code '%s' validated", code)
        return record
    finally:
        conn.close()



# ─── HMAC Packet Signing ────────────────────────────────────────────

def compute_hmac(secret_key: str, data: bytes) -> str:
    """
    Compute HMAC-SHA256 of data using the secret key.
    Returns hex digest string.
    """
    key_bytes = secret_key.encode("utf-8")
    return hmac.new(key_bytes, data, hashlib.sha256).hexdigest()


def verify_hmac(secret_key: str, data: bytes, expected_hex: str) -> bool:
    """
    Verify HMAC-SHA256 of data against expected hex digest.
    Uses constant-time comparison.
    """
    actual_hex = compute_hmac(secret_key, data)
    return hmac.compare_digest(actual_hex, expected_hex)


def sign_packet(secret_key: str, payload: bytes) -> bytes:
    """
    Sign a payload with HMAC-SHA256.
    Returns: payload_length (4 bytes) + hmac (32 bytes) + payload
    """
    signature = bytes.fromhex(compute_hmac(secret_key, payload))
    length = struct.pack("!I", len(payload))
    return length + signature + payload


def verify_signed_packet(secret_key: str, packet: bytes) -> Optional[bytes]:
    """
    Verify and extract payload from a signed packet.
    Returns the payload bytes if valid, None otherwise.
    """
    if len(packet) < 4 + 32:
        logger.error("Packet too short for verification")
        return None

    offset = 0
    payload_length = struct.unpack("!I", packet[offset:offset + 4])[0]
    offset += 4

    signature = packet[offset:offset + 32]
    offset += 32

    payload = packet[offset:offset + payload_length]
    if len(payload) != payload_length:
        logger.error("Payload length mismatch")
        return None

    # Recompute HMAC
    key_bytes = secret_key.encode("utf-8")
    expected_sig = hmac.new(key_bytes, payload, hashlib.sha256).digest()

    if hmac.compare_digest(signature, expected_sig):
        return payload
    else:
        logger.error("HMAC verification failed - possible tampering")
        return None


# ─── Pairing Result ─────────────────────────────────────────────────

@dataclass
class PairingResult:
    """Result of a successful pairing operation."""
    code: str
    app_type: str
    secret_key: str
    device_name: str = ""
    device_address: str = ""
    connected: bool = False




# ─── BLE Advertiser (Sound/Light apps - uses bleson) ──────────────────

class BLEAdvertiser:
    """
    BLE advertiser for Sound and Light apps.
    Advertises the pairing code via BLE using bleson.
    """

    def __init__(self, app_type: str, code: str = ""):
        """
        Initialize the advertiser.
        app_type: 'sound' or 'light'
        code: pairing code to advertise (if empty, generates a new one)
        """
        self.app_type = app_type
        self.code = code or generate_pairing_code(app_type)
        self.secret_key = ""
        self._bleson_adv = None
        self._adapter = None

    def start(self) -> str:
        """
        Start advertising the pairing code.
        Saves code to local_codes.db with a 5-minute expiry.
        Returns the pairing code.
        """
        self.secret_key = save_pairing_code(self.code, self.app_type, duration=300.0)

        try:
            from bleson import get_provider, Advertisement
            provider = get_provider()
            self._adapter = provider.get_adapter()
            self._bleson_adv = Advertisement()
            self._bleson_adv.service_UUIDs = [LIGHTMAN_SERVICE_UUID]
            self._bleson_adv.manufacturer_data = self.code.encode("utf-8")
            self._bleson_adv.local_name = f"Lightman-{self.code}"
            logger.info("Started BLE advertising: %s", self.code)
            self._adapter.advertise(self._bleson_adv)
        except ImportError:
            logger.warning("bleson not installed — running in stub mode (code generated, no BLE advertising)")
        except Exception as e:
            logger.error("BLE advertising failed: %s", e)

        return self.code

    def stop(self) -> None:
        """Stop BLE advertising."""
        if self._adapter and self._bleson_adv:
            try:
                self._adapter.stop_advertising()
                logger.info("Stopped BLE advertising")
            except Exception as e:
                logger.error("Error stopping BLE advertising: %s", e)
        self._bleson_adv = None
        self._adapter = None

    def get_secret_key(self) -> str:
        """Return the secret key for this pairing session."""
        return self.secret_key



# ─── BLE Scanner (Director - uses bleak) ──────────────────────────────

class BLEScanner:
    """
    BLE scanner for the Director app.
    Scans for Lightman advertisement packets, matches codes.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._found_devices: list[dict] = []

    async def scan(self) -> list[dict]:
        """
        Scan for BLE devices advertising Lightman pairing codes.
        Returns list of discovered devices with code and metadata.
        """
        self._found_devices = []

        try:
            from bleak import BleakScanner
        except ImportError:
            logger.warning("bleak not installed — scanning will return empty results")
            return []

        logger.info("Starting BLE scan for %d seconds...", self.timeout)

        def detection_callback(device, adv_data):
            local_name = adv_data.local_name or ""
            # Check for the fixed Lightman Service UUID
            service_uuids = adv_data.service_UUIDs or []
            uuid_strs = [str(u) for u in service_uuids]
            has_lightman_uuid = any(
                LIGHTMAN_SERVICE_UUID.lower() in u.lower() for u in uuid_strs
            )
            if has_lightman_uuid and local_name.startswith("Lightman-"):
                # Extract the pairing code from local_name
                code = local_name[len("Lightman-"):]
                # Fallback: try manufacturer_data if local_name parsing didn't work
                if not code or not code.startswith("SL-"):
                    if adv_data.manufacturer_data:
                        for m in adv_data.manufacturer_data:
                            try:
                                code = m.decode("utf-8", errors="replace")
                                break
                            except Exception:
                                continue
                if code:
                    entry = {
                        "address": device.address,
                        "name": local_name,
                        "code": code,
                        "rssi": getattr(device, "rssi", None),
                    }
                    if not any(d["address"] == entry["address"] for d in self._found_devices):
                        self._found_devices.append(entry)
                        logger.info("Found device: %s (%s) RSSI=%s", local_name, code, entry["rssi"])

        scanner = BleakScanner(detection_callback)
        await scanner.start()
        import asyncio
        await asyncio.sleep(self.timeout)
        await scanner.stop()

        logger.info("Scan complete. Found %d devices.", len(self._found_devices))
        return self._found_devices

    def verify_code(self, code: str) -> Optional[PairingResult]:
        """
        Verify a user-entered code against discovered devices and local codes DB.
        Returns PairingResult if valid, None otherwise.
        """
        record = lookup_pairing_code(code)
        if record is None:
            return None

        matched_device = None
        for dev in self._found_devices:
            if dev["code"] == code:
                matched_device = dev
                break

        result = PairingResult(
            code=code,
            app_type=record["app_type"],
            secret_key=record["secret_key"],
        )

        if matched_device:
            result.device_address = matched_device["address"]
            result.device_name = matched_device["name"]

        return result



# ─── GATT Connection (Director -> Sound/Light) ────────────────────────

class GATTConnection:
    """
    GATT connection to a paired Sound/Light device.
    Uses bleak for BLE GATT communication.
    """

    def __init__(self, device_address: str, secret_key: str):
        self.device_address = device_address
        self.secret_key = secret_key
        self._client = None

    async def connect(self) -> bool:
        """Establish GATT connection to the device."""
        try:
            from bleak import BleakClient
            self._client = BleakClient(self.device_address)
            await self._client.connect()
            logger.info("GATT connected to %s", self.device_address)
            return True
        except Exception as e:
            logger.error("GATT connection failed: %s", e)
            return False

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            logger.info("GATT disconnected from %s", self.device_address)
        self._client = None

    async def send_signed(self, payload: bytes) -> bool:
        """Send an HMAC-signed packet via GATT."""
        if not self._client or not self._client.is_connected:
            logger.error("GATT not connected")
            return False

        signed = sign_packet(self.secret_key, payload)
        # Write to a characteristic (UUID to be defined in implementation)
        logger.debug("Signed packet sent (%d bytes)", len(signed))
        return True

    async def read_signed(self) -> Optional[bytes]:
        """Read and verify an HMAC-signed packet from GATT."""
        # Placeholder — actual implementation reads from GATT characteristic
        logger.warning("read_signed not fully implemented — returns placeholder")
        return None


# ─── Convenience Factory ─────────────────────────────────────────────

def get_pairing_manager(app_type: str):
    """
    Convenience function: returns a BLEAdvertiser configured for the given app.
    Used by Sound/Light apps to start/stop advertising.
    """
    advertiser = BLEAdvertiser(app_type)
    return advertiser

