#!/usr/bin/env python3
"""
Lightman Fixture Manager
========================
Loads, searches, and queries the fixtures catalog.
Provides beam geometry lookup for the 3D scene.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from shared.config import get_logger, FIXTURES_DIR

logger = get_logger("fixture_manager")


class FixtureManager:
    """Load and query the fixtures catalog from fixtures_catalog.json."""

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or (FIXTURES_DIR / "fixtures_catalog.json")
        self._catalog: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """Load the fixture catalog from JSON."""
        try:
            with open(self.catalog_path, "r") as f:
                self._catalog = json.load(f)
            self._by_id = {fx["id"]: fx for fx in self._catalog}
            logger.info(f"Loaded {len(self._catalog)} fixtures from catalog")
        except FileNotFoundError:
            logger.warning(f"Fixture catalog not found: {self.catalog_path}")
            logger.warning("Run: python scripts/generate_databases.py")
            self._catalog = []
            self._by_id = {}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading fixture catalog: {e}")
            self._catalog = []
            self._by_id = {}

    @property
    def all(self) -> list[dict]:
        return self._catalog

    def get(self, fixture_id: str) -> Optional[dict]:
        """Look up a fixture by its ID."""
        return self._by_id.get(fixture_id)

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Search fixtures by manufacturer, name, or type (case-insensitive)."""
        q = query.lower().strip()
        results = []
        for fx in self._catalog:
            name_match = q in fx.get("name", "").lower()
            mfr_match = q in fx.get("manufacturer", "").lower()
            type_match = q in fx.get("type", "").lower()
            if name_match or mfr_match or type_match:
                results.append(fx)
                if len(results) >= limit:
                    break
        return results

    def by_manufacturer(self, manufacturer: str) -> list[dict]:
        """Return all fixtures from a given manufacturer."""
        return [fx for fx in self._catalog
                if fx.get("manufacturer", "").lower() == manufacturer.lower()]

    def by_type(self, ftype: str) -> list[dict]:
        """Return all fixtures of a given type (e.g., 'spot', 'wash', 'beam')."""
        return [fx for fx in self._catalog
                if fx.get("type", "").lower() == ftype.lower()]

    def get_beam_angle(self, fixture_id: str) -> float:
        """Return the beam angle (degrees) for a fixture, defaulting to 25.0."""
        fx = self.get(fixture_id)
        if fx:
            return float(fx.get("beam_angle", 25.0))
        return 25.0

    def get_beam_geometry(self, fixture_id: str) -> dict:
        """
        Return a geometry descriptor for rendering a fixture's beam in 3D.

        Includes beam_angle (degrees), zoom_range, and DMX channel count
        so the 3D view can adjust beam cone width dynamically.
        """
        fx = self.get(fixture_id)
        if not fx:
            return {
                "beam_angle": 25.0,
                "zoom_range": "N/A",
                "dmx_channels": 32,
                "type": "par",
            }
        return {
            "beam_angle": float(fx.get("beam_angle", 25.0)),
            "zoom_range": fx.get("zoom_range", "N/A"),
            "dmx_channels": fx.get("dmx_channels", 32),
            "type": fx.get("type", "par"),
        }


# ─── Convenience: module-level singleton ────────────────────────────

_default_manager: Optional[FixtureManager] = None


def get_fixture_manager() -> FixtureManager:
    """Return a cached FixtureManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = FixtureManager()
    return _default_manager
