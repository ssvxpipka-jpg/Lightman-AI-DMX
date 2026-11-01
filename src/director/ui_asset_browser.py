"""Asset browser widget for Lightman Director."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, QEvent, QPoint, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

CATALOG_PATH = Path("fixtures_db/fixtures_catalog.json")

CATEGORY_ORDER = [
    "Moving Heads",
    "LED Bars",
    "Lasers",
    "Strobes",
    "Dimmers",
    "Trusses",
    "Stands",
    "Curtains",
    "Other",
]

HARDCODED_FIXTURES = [
    {
        "id": "TRUSS-2M",
        "name": "Truss 2m",
        "type": "truss",
        "manufacturer": "Generic",
        "dmx_channels": 0,
        "position": [0, 0, 0],
    },
    {
        "id": "TRUSS-3M",
        "name": "Truss 3m",
        "type": "truss",
        "manufacturer": "Generic",
        "dmx_channels": 0,
        "position": [0, 0, 0],
    },
    {
        "id": "STAND-1M",
        "name": "Stand 1m",
        "type": "stand",
        "manufacturer": "Generic",
        "dmx_channels": 0,
        "position": [0, 0, 0],
    },
]


def _category_for(fixture: dict) -> str:
    ftype = (fixture.get("type") or "").lower()
    if "moving" in ftype or "head" in ftype or ftype in ("beam", "spot", "wash", "hybrid"):
        return "Moving Heads"
    if "led" in ftype or ftype in ("par", "led_bar"):
        return "LED Bars"
    if "laser" in ftype:
        return "Lasers"
    if "strobe" in ftype:
        return "Strobes"
    if "dimmer" in ftype:
        return "Dimmers"
    if "truss" in ftype:
        return "Trusses"
    if "stand" in ftype:
        return "Stands"
    if "curtain" in ftype:
        return "Curtains"
    return "Other"


class AssetBrowserWidget(QWidget):
    """Searchable tree of fixtures loaded from fixtures_db."""

    fixture_selected = Signal(dict)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._fixtures: list[dict] = []
        self._build_ui()
        self._load_catalog()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search fixtures…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabels(["Fixture", "Type"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setDragEnabled(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        # SINGLE CLICK — itemClicked fires on left-click release.
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.installEventFilter(self)
        layout.addWidget(self.tree, 1)

    # ------------------------------------------------------------------
    # Catalog loading
    # ------------------------------------------------------------------

    def _load_catalog(self) -> None:
        self.tree.clear()
        self._fixtures = []

        raw = []
        if CATALOG_PATH.exists():
            data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                raw = data
            elif isinstance(data, dict):
                raw = data.get("fixtures", data.get("items", []))
        raw = [dict(f) for f in raw if isinstance(f, dict)]
        # Hardcoded truss/stand items so something can always be spawned.
        raw.extend(dict(f) for f in HARDCODED_FIXTURES)
        self._fixtures = raw
        self._populate_tree()

    def _populate_tree(self) -> None:
        self.tree.clear()

        grouped: dict[str, list[dict]] = {}
        for fixture in self._fixtures:
            grouped.setdefault(_category_for(fixture), []).append(fixture)

        for category in CATEGORY_ORDER:
            entries = grouped.get(category)
            if not entries:
                continue

            parent = QTreeWidgetItem(self.tree, [category, ""])
            parent.setExpanded(True)
            parent.setFlags(Qt.ItemFlag.ItemIsEnabled)

            for fixture in entries:
                name = str(fixture.get("name") or fixture.get("id") or "Unnamed")
                ftype = str(fixture.get("type") or "")
                child = QTreeWidgetItem(parent, [name, ftype])
                # Full dict stored on the item — no reconstruction on click.
                child.setData(0, Qt.ItemDataRole.UserRole, fixture)

        # Re-apply current search filter (if any)
        self._apply_filter(self.search.text())

    # ------------------------------------------------------------------
    # Search filtering
    # ------------------------------------------------------------------

    def _apply_filter(self, text: str) -> None:
        needle = (text or "").strip().lower()
        root = self.tree.invisibleRootItem()

        for i in range(root.childCount()):
            category_item = root.child(i)
            any_visible = False
            for j in range(category_item.childCount()):
                child = category_item.child(j)
                haystack = (child.text(0) + " " + child.text(1)).lower()
                visible = (not needle) or (needle in haystack)
                child.setHidden(not visible)
                if visible:
                    any_visible = True
            category_item.setHidden(not any_visible)

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(payload, dict):
            self.fixture_selected.emit(dict(payload))

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event) -> None:
        if obj is self.tree:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._drag_start_pos = event.position()
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    if hasattr(self, "_drag_start_pos"):
                        diff = event.position() - self._drag_start_pos
                        if diff.manhattanLength() >= QApplication.startDragDistance():
                            self._start_drag()
                            return True
        return super().eventFilter(obj, event)

    def _start_drag(self) -> None:
        item = self.tree.currentItem()
        if not item:
            return
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(payload, dict):
            return

        mime_data = QMimeData()
        mime_data.setData(
            "application/x-lightman-fixture",
            json.dumps(payload).encode("utf-8"),
        )

        drag = QDrag(self.tree)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)
