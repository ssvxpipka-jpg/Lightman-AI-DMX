"""
Lightman Blackout Guard
========================
Implements the blackout safety logic for lighting control.

Blackout Rules:
    - 0%:    AI holds 0%. No change.
    - 1-5%:  AI does NOT increase brightness.
    - >5%:   AI works within limits.

In Blackout state, Live Light and Tracking agents are MUTED.

Modes:
    - full_auto:    AI takes full control; 5% standby for safety
    - assist:       Human in-the-loop; AI intercepts on errors > 15%
    - follow_only:  PAN/TILT + beat only; minimal AI intervention;
                    Blackout is strictly ignored by AI (pass-through)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from shared.config import get_logger

logger = get_logger("blackout")


@dataclass
class BlackoutState:
    """Current state of the blackout guard."""
    level: float = 0.0           # Current lighting level (0.0 to 1.0)
    mode: str = "assist"         # Current operating mode
    ai_enabled: bool = True      # Whether AI is allowed to control lights
    live_light_muted: bool = False
    tracking_muted: bool = False
    last_update: float = 0.0


class BlackoutGuard:
    """
    Enforces blackout rules and mode-based AI behavior.
    """

    # Level thresholds
    LEVEL_ZERO_THRESHOLD = 0.0
    LEVEL_LOW_MIN = 0.01      # 1%
    LEVEL_LOW_MAX = 0.05      # 5%
    LEVEL_NORMAL_MIN = 0.05   # 5%

    def __init__(self, mode: str = "assist"):
        self.state = BlackoutState(mode=mode)
        self._update_mode_state(mode)

    def _update_mode_state(self, mode: str) -> None:
        """Update internal state based on operating mode."""
        self.state.mode = mode

        if mode == "full_auto":
            self.state.ai_enabled = True
            self.state.live_light_muted = False
            self.state.tracking_muted = False
        elif mode == "assist":
            self.state.ai_enabled = True
            self.state.live_light_muted = False
            self.state.tracking_muted = False
        elif mode == "follow_only":
            # In follow_only, Blackout is strictly ignored — AI is effectively
            # off; only PAN/TILT + beat drive lights directly.
            self.state.ai_enabled = False
            self.state.live_light_muted = False  # Tracking passes through
            self.state.tracking_muted = False    # Tracking passes through
        else:
            logger.warning("Unknown mode '%s', defaulting to 'assist'", mode)
            self.state.mode = "assist"
            self.state.ai_enabled = True
            self.state.live_light_muted = False
            self.state.tracking_muted = False

    def set_mode(self, mode: str) -> None:
        """Change the operating mode."""
        logger.info("Mode changed: %s -> %s", self.state.mode, mode)
        self._update_mode_state(mode)

    def set_level(self, level: float) -> None:
        """
        Set the current lighting level (0.0 to 1.0).
        Updates blackout state accordingly.

        SACRED RULE: At 0% (Blackout), AI MUST output 0% and
        Tracking MUST be MUTED — applies to ALL modes unconditionally.
        The only exception: pre-show config allows a standby light (>0%).
        """
        level = max(0.0, min(1.0, level))
        old_level = self.state.level
        self.state.level = level

        # ── SACRED RULE: 0% -> 0% applies to ALL modes ──────────────
        if level <= self.LEVEL_ZERO_THRESHOLD:
            # 0%: AI holds 0%, mute Live Light and Tracking — UNCONDITIONAL
            self.state.ai_enabled = False
            self.state.live_light_muted = True
            self.state.tracking_muted = True
            logger.info("BLACKOUT: Level at 0%% — AI holds 0%%, Live Light/Tracking MUTED")
            return

        # ── 1-5%: AI does NOT increase brightness ────────────────────
        if level <= self.LEVEL_LOW_MAX:
            self.state.live_light_muted = False
            self.state.tracking_muted = False
            if level > old_level:
                # AI wants to increase — BLOCK it
                self.state.ai_enabled = False
                logger.info("BLACKOUT: Level %.1f%% — AI does NOT increase brightness", level * 100)
            else:
                # Maintaining or decreasing — allow AI to adjust down
                self.state.ai_enabled = True
            return

        # ── >5%: AI works within limits ─────────────────────────────
        # In follow_only mode, AI is never enabled (only PAN/TILT + beat)
        if self.state.mode == "follow_only":
            self.state.ai_enabled = False
        else:
            self.state.ai_enabled = True
        self.state.live_light_muted = False
        self.state.tracking_muted = False
        logger.debug("Level %.1f%% — AI working within limits", level * 100)

    def can_ai_adjust(self) -> bool:
        """
        Check if AI is currently allowed to adjust lighting.
        Returns False during blackout or in follow_only mode.
        """
        return self.state.ai_enabled

    def is_blackout(self) -> bool:
        """Check if we're in a blackout state (level <= 5%)."""
        return self.state.level <= self.LEVEL_LOW_MAX

    def get_adjusted_level(self, requested_level: float) -> float:
        """
        Apply blackout rules to a requested light level.
        Returns the clamped level that respects current blackout state.

        SACRED RULE: At 0% (Blackout), ALL levels are clamped to 0%,
        regardless of mode or who is requesting.
        """
        requested_level = max(0.0, min(1.0, requested_level))

        # SACRED RULE: 0% level → always 0% output, no exceptions
        if self.state.level <= self.LEVEL_ZERO_THRESHOLD:
            logger.debug("BLACKOUT: clamping all output to 0%%")
            return 0.0

        if not self.can_ai_adjust():
            # AI cannot increase — return current level if request is higher
            if self.state.mode == "follow_only":
                # follow_only: AI doesn't control levels, but 0% still applies
                # (already handled above)
                return requested_level
            if requested_level > self.state.level:
                logger.debug("Blackout: clamping %.1f%% -> %.1f%%",
                             requested_level * 100, self.state.level * 100)
                return self.state.level
            return requested_level

        return requested_level

    def get_state(self) -> BlackoutState:
        """Return a copy of the current blackout state."""
        return self.state
