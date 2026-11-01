"""
Fixture library panel — tree of fixtures grouped by category.

Loads every fixture from fixtures_db/fixtures_catalog.json, groups them
by their `type` field, and adds a few hardcoded structural elements
(trusses, stands, curtains). A search bar filters leaves as you type.
"""

import json
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel,
)

# ---------------------------------------------------------------------------
# Type normalisation
# ---------------------------------------------------------------------------

_TYPE_TO_CATEGORY = {
    "moving_head": "Moving Heads",
    "movinghead": "Moving Heads",
    "moving head": "Moving Heads",
    "moving heads": "Moving Heads",
    "moving_heads": "Moving Heads",
    "led_bar": "LED Bars",
    "ledbar": "LED Bars",
    "led bar": "LED Bars",
    "led bars": "LED Bars",
    "led_bars": "LED Bars",
    "led": "LED Bars",
    "laser": "Lasers",
    "lasers": "Lasers",
    "strobe": "Strobes",
    "strobes": "Strobes",
    "dimmer": "Dimmers",
    "dimmers": "Dimmers",
    "truss": "Trusses",
    "trusses": "Trusses",
    "stand": "Stands",
    "stands": "Stands",
    "curtain": "Curtains",
    "curtains": "Curtains",
}

_CATEGORIES = [
    "Moving Heads", "LED Bars", "Lasers", "Strobes", "Dimmers",
    "Trusses", "Stands", "Curtains",
]

_HARDCODED = {
    "Trusses": [
        {
            "type": "truss",
            "name": "Truss 2m",
            "position": [0.0, 0.0, 0.0],
            "length": 2.0,
            "height": 0.3,
            "width": 0.3,
        },
        {
            "type": "truss",
            "name": "Truss 4m",
            "position": [0.0, 0.0, 0.0],
            "length": 4.0,
            "height": 0.3,
            "width": 0.3,
        },
    ],
    "Stands": [
        {
            "type": "stand",
            "name": "Stand 1m",
            "position": [0.0, 0.0, 0.0],
            "height": 1.0,
        },
    ],
    "Curtains": [
        {
            "type": "curtain",
            "name": "Black Curtain",
            "position": [0.0, 0.0, 0.0],
            "width": 6.0,
            "height": 4.0,
        },
    ],
}


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _fixtures_path() -> str:
    """Absolute path to fixtures_db/fixtures_catalog.json."""
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        )
    )
    return os.path.join(project_root, "fixtures_db", "fixtures_catalog.json")


def _load_catalogue():
    """Return a list of fixture dicts from fixtures_catalog.json."""
    path = _fixtures_path()
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return list(data.get("fixtures", []))
    if isinstance(data, list):
        return data
    return []


def _normalize_type(raw) -> str:
    key = str(raw or "").lower().strip()
    return _TYPE_TO_CATEGORY.get(key, None)


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class FixtureLibraryPanel(QWidget):
    """Left panel: searchable tree of all fixtures."""

    fixture_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Fixture Library")
        title.setObjectName("Section")
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search fixtures…")
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree, 1)

        self._populate_tree()

    # ------------------------------------------------------------------ data

    def _populate_tree(self):
        self.tree.clear()
        cat_items = {}

        for name in _CATEGORIES:
            cat_item = QTreeWidgetItem([name])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            self.tree.addTopLevelItem(cat_item)
            cat_items[name] = cat_item

        catalogue = _load_catalogue()
        for fx in catalogue:
            category = _normalize_type(fx.get("type", ""))
            if category is None:
                continue
            label = fx.get("name") or fx.get("id") or "fixture"
            child = QTreeWidgetItem([str(label)])
            child.setData(0, Qt.UserRole, fx)
            cat_items[category].addChild(child)

        for category, items in _HARDCODED.items():
            for fx in items:
                child = QTreeWidgetItem([fx["name"]])
                child.setData(0, Qt.UserRole, fx)
                cat_items[category].addChild(child)

        self.tree.expandAll()

    # ----------------------------------------------------------------- slots

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        payload = item.data(0, Qt.UserRole)
        if payload is None:
            return
        self.fixture_selected.emit(payload)

    def _on_search_changed(self, text: str):
        query = text.strip().lower()
        root = self.tree.invisibleRootItem()

        for i in range(root.childCount()):
            cat = root.child(i)
            cat_visible = False

            for j in range(cat.childCount()):
                leaf = cat.child(j)
                match = (not query) or (query in leaf.text(0).lower())
                leaf.setHidden(not match)
                if match:
                    cat_visible = True

            cat.setHidden(not cat_visible and bool(query))
            if query and cat_visible:
                cat.setExpanded(True)