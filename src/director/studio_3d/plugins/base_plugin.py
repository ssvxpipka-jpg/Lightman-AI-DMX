"""Base class for studio 3D plugins."""

from __future__ import annotations

from PySide6.QtCore import QObject


class BasePlugin(QObject):
    """Base class for all studio 3D plugins.

    Plugins can hook into the editor lifecycle, provide custom tools,
    or extend the UI.
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_activate(self) -> None:
        """Called when the plugin is activated by the manager."""
        pass