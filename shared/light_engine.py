"""
Lightman Light Engine
=====================
Handles the three operating modes and coordinates with the BlackoutGuard.

Modes:
    - full_auto:    AI takes full control of all lighting.
                    5% standby level for safety when idle.
    - assist:       Human operator controls primary lights; AI intercepts
                    when errors exceed the intercept threshold (>15%).
    - follow_only:  PAN/TILT movement driven by beat/tracking.
                    AI intervention is disabled. Blackout is ignored.

The LightEngine acts as the central authority for light level decisions,
consulting the BlackoutGuard before allowing AI to adjust anything.
"""

from __future__ import annotations

from typing import Any, Optional

from shared.blackout_guard import BlackoutGuard
from shared.config import get_logger

logger = get_logger("light_engine")


class LightEngine:
    """
    Central light control engine coordinating modes and blackout rules.
    """

    MODES = {
        "full_auto": {
            "name": "Full Auto",
            "description": "AI takes full control; 5% standby for safety",
            "standby_level": 0.05,
            "ai_enabled": True,
        },
        "assist": {
            "name": "Assist",
            "description": "Human in-the-loop; AI intercepts on errors > 15%",
            "standby_level": 0.05,
            "ai_enabled": True,
        },
        "follow_only": {
            "name": "Follow Only",
            "description": "PAN/TILT + beat only; minimal AI intervention",
            "standby_level": 0.0,
            "ai_enabled": False,
        },
    }

    def __init__(self, mode: str = "assist"):
        self.mode = mode if mode in self.MODES else "assist"
        self.blackout = BlackoutGuard(mode=self.mode)
        self._current_level: float = 0.0
        self._target_level: float = 0.0
        logger.info("LightEngine initialized in %s mode", self.mode)

    def set_mode(self, mode: str) -> bool:
        """
        Switch the operating mode.
        """
        if mode not in self.MODES:
            logger.error("Unknown mode: %s", mode)
            return False
        logger.info("Switching mode: %s -> %s", self.mode, mode)
        self.mode = mode
        self.blackout.set_mode(mode)
        return True

    def set_level(self, level: float) -> float:
        """
        Set the target light level (0.0 to 1.0).
        The actual level is clamped by blackout rules.
        Returns the effective (clamped) level.
        """
        level = max(0.0, min(1.0, level))
        self._target_level = level
        self.blackout.set_level(level)
        effective = self.blackout.get_adjusted_level(level)
        self._current_level = effective
        return effective

    def ai_request_level(self, requested_level: float) -> float:
        """
        AI requests a light level change.
        The BlackoutGuard may reject or clamp this based on blackout state.
        Returns the effective level that was applied.
        """
        if not self.blackout.can_ai_adjust():
            if self.mode == "follow_only":
                # follow_only: AI doesn't control levels at all
                logger.debug("follow_only mode — AI level request ignored")
                return self._current_level
            # Blackout active — AI cannot increase
            clamped = self.blackout.get_adjusted_level(requested_level)
            self._current_level = clamped
            logger.debug("AI level request %.1f%% -> clamped to %.1f%%",
                         requested_level * 100, clamped * 100)
            return clamped

        effective = self.blackout.get_adjusted_level(requested_level)
        self._current_level = effective
        return effective

    def direct_request_level(self, requested_level: float) -> float:
        """
        Direct (non-AI) request to set a light level.
        Used by Live Light and tracking in follow_only mode.

        SACRED RULE: Even direct requests are clamped to 0%
        when the blackout level is 0%. No light at all in blackout.
        """
        level = max(0.0, min(1.0, requested_level))

        # SACRED RULE: 0% blackout clamps ALL output to 0%
        if self.blackout.state.level <= 0.0:
            level = 0.0
            logger.debug("Direct request in BLACKOUT — clamped to 0%%")

        self._target_level = level
        self._current_level = level
        logger.debug("Direct level request: %.1f%%", level * 100)
        return level

    def get_mode_info(self) -> dict[str, Any]:
        """Return info about the current mode."""
        info = self.MODES[self.mode].copy()
        info["current_level"] = self._current_level
        info["target_level"] = self._target_level
        info["is_blackout"] = self.blackout.is_blackout()
        info["ai_can_adjust"] = self.blackout.can_ai_adjust()
        return info

    def get_current_level(self) -> float:
        """Return the current effective light level."""
        return self._current_level

    def get_standby_level(self) -> float:
        """Return the standby level for the current mode."""
        return self.MODES[self.mode]["standby_level"]
