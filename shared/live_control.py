"""
Lightman Live Control Interface (MIDI Stub)
============================================
STUB — skeleton only. MIDI implementation to be added in Lightman 1.1.

Provides a LiveControlInterface that can be extended to support:
- MIDI control surfaces (sliders, knobs, pads)
- MIDI output to control physical lighting desks
- OSC-to-MIDI bridging
- Real-time parameter mapping
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from shared.config import get_logger

logger = get_logger("live_control")


class LiveControlInterface:
    """
    Stub interface for live MIDI control surface integration.
    """

    def __init__(self) -> None:
        self._midi_in = None
        self._midi_out = None
        self._connected = False
        logger.info("LiveControlInterface initialized (STUB MODE)")

    def connect(self) -> bool:
        """Connect to a MIDI control surface."""
        # TODO: Implement MIDI device discovery and connection
        logger.warning("MIDI connect not implemented — stub mode")
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from the MIDI device."""
        # TODO: Close MIDI ports
        logger.warning("MIDI disconnect not implemented — stub mode")
        self._connected = False

    def send_midi(self, note: int, velocity: int, channel: int = 0) -> None:
        """
        Send a MIDI note on message.
        """
        # TODO: Forward MIDI message to connected device
        logger.debug("STUB: send_midi(note=%d, velocity=%d, channel=%d)", note, velocity, channel)

    def receive_midi(self) -> Optional[tuple[int, int, int]]:
        """
        Receive a MIDI message.
        Returns (note, velocity, channel) or None.
        """
        # TODO: Poll MIDI input port
        logger.debug("STUB: receive_midi() — not implemented")
        return None

    def map_fixture_to_knob(self, fixture_id: str, parameter: str, knob_index: int) -> None:
        """
        Map a fixture parameter to a physical MIDI knob.
        """
        # TODO: Store mapping in data structure for runtime use
        logger.debug("STUB: map_fixture_to_knob(fixture=%s, param=%s, knob=%d)",
                      fixture_id, parameter, knob_index)

    @property
    def is_connected(self) -> bool:
        return self._connected
