"""Plugin manager for discovering and loading studio 3D plugins."""

from __future__ import annotations

import importlib
import os
from pathlib import Path

from PySide6.QtCore import QObject

from .base_plugin import BasePlugin


class PluginManager(QObject):
    """Manages discovery, loading, and lifecycle of studio 3D plugins."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load_plugins(self, plugin_dir: str) -> None:
        """Scan *plugin_dir* for Python modules and load them as plugins.

        Each module is expected to expose a ``Plugin`` class that inherits
        from ``BasePlugin``.  The plugin is instantiated and ``on_activate()``
        is called.

        Args:
            plugin_dir: directory path relative to the project root containing
                        plugin .py files.
        """
        base = Path(plugin_dir)
        if not base.exists():
            return

        for p in sorted(base.rglob("*.py")):
            if p.name == "__init__.py":
                continue

            module_path = p.relative_to(base.parent)
            module_str = f"{module_path.parent.name}.{module_path.stem}"
            try:
                mod = importlib.import_module(module_str)
                if hasattr(mod, "Plugin"):
                    cls = mod.Plugin
                    if issubclass(cls, BasePlugin) and cls is not BasePlugin:
                        instance = cls(name=cls.__name__)
                        instance.on_activate()
            except Exception as exc:  # noqa: BLE001
                pass  # silently skip broken plugins