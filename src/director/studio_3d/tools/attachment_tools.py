"""Attachment tools for the studio 3D editor."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class AttachmentTools(QObject):
    """Tools for attaching/detaching fixtures to trusses and other structures."""

    # ------------------------------------------------------------------
    # Attachment operations
    # ------------------------------------------------------------------

    def attach_fixture_to_truss(
        self, fixture_name: str, truss_name: str
    ) -> None:
        """Attach a fixture to a truss at the specified location.

        Args:
            fixture_name: name of the fixture to attach.
            truss_name: name of the truss to attach to.
        """
        pass

    def detach_fixture(self, fixture_name: str) -> None:
        """Detach a fixture from its current parent.

        Args:
            fixture_name: name of the fixture to detach.
        """
        pass