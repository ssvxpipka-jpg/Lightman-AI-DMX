"""
Lightman Audio Sources (Stubs)
===============================
STUB — skeleton only. Implementations to be added in later stages.

Provides audio source interfaces for:
- Bluetooth audio relay (receiving audio from paired devices)
- Microphone array capture with speech-to-text
"""

from __future__ import annotations

import logging
from typing import Optional

from shared.config import get_logger

logger = get_logger("audio_source")


class BluetoothRelaySource:
    """
    Stub: Receives audio stream from a paired Bluetooth device.
    """

    def __init__(self) -> None:
        self._address: str = ""
        self._connected: bool = False
        logger.info("BluetoothRelaySource initialized (STUB MODE)")

    def connect(self, device_address: str) -> bool:
        """
        Connect to a Bluetooth audio source.
        """
        # TODO: Implement RFCOMM or A2DP connection via bleak/bleson
        logger.warning("Bluetooth connect not implemented — stub mode")
        self._address = device_address
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from the Bluetooth device."""
        # TODO: Close Bluetooth connection
        logger.warning("Bluetooth disconnect not implemented — stub mode")
        self._connected = False

    def get_audio_frame(self, frame_size: int = 1024) -> Optional[bytes]:
        """
        Retrieve the next audio frame.
        Returns raw PCM audio bytes or None if no data.
        """
        # TODO: Implement audio frame reading from Bluetooth stream
        logger.debug("STUB: get_audio_frame(frame_size=%d) — not implemented", frame_size)
        return None

    @property
    def is_connected(self) -> bool:
        return self._connected


class MicrophoneSTTSource:
    """
    Stub: Captures audio from a microphone array and provides STT input.
    """

    def __init__(self, sample_rate: int = 44100, channels: int = 2) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._stream = None
        self._running: bool = False
        logger.info("MicrophoneSTTSource initialized (STUB MODE)")

    def request_permission(self) -> bool:
        """
        Request microphone access permission from the OS.
        Cross-platform: handles macOS, Windows, Linux permission dialogs.
        """
        # TODO: Use sounddevice or pyaudio to request mic access
        # macOS: needs microphone permission in System Settings
        # Windows: needs microphone access in Privacy Settings
        # Linux: depends on PulseAudio/PipeWire configuration
        logger.warning("Microphone permission not implemented — stub mode")
        return True

    def start(self) -> bool:
        """
        Start the microphone capture stream.
        """
        # TODO: Initialize sounddevice or pyaudio stream
        logger.warning("Microphone start not implemented — stub mode")
        self._running = True
        return True

    def stop(self) -> None:
        """
        Stop the microphone capture stream.
        """
        # TODO: Close audio stream
        logger.warning("Microphone stop not implemented — stub mode")
        self._running = False

    def get_audio_frame(self, frame_size: int = 1024) -> Optional[bytes]:
        """
        Retrieve the next audio frame from the microphone.
        """
        # TODO: Read from audio stream
        logger.debug("STUB: get_audio_frame(frame_size=%d) — not implemented", frame_size)
        return None

    def get_speech_text(self) -> Optional[str]:
        """
        Convert current microphone input to text (speech-to-text).
        """
        # TODO: Integrate with Whisper or Vosk for STT
        logger.debug("STUB: get_speech_text() — not implemented")
        return None

    @property
    def is_running(self) -> bool:
        return self._running
