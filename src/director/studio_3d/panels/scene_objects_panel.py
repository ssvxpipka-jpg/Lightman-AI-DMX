"""Scene objects panel — list of currently spawned fixtures on stage."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QAbstractItemView,
)


class SceneObjectsPanel(QWidget):
    object_removed = Signal(str)
    object_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Scene Objects")
        title.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #f0a500;"
        )
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget, 1)

        buttons = QHBoxLayout()
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        buttons.addWidget(self.delete_btn)
        layout.addLayout(buttons)

    # ------------------------------------------------------------- public API

    def add_object(self, name: str):
        if not name:
            return
        self.list_widget.addItem(name)

    def remove_object(self, name: str):
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.text() == name:
                self.list_widget.takeItem(row)
                return

    def clear(self):
        self.list_widget.clear()

    # ----------------------------------------------------------------- slots

    def _on_delete_clicked(self):
        item = self.list_widget.currentItem()
        if item is None:
            return
        name = item.text()
        self.object_removed.emit(name)
        self.list_widget.takeItem(self.list_widget.row(item))

    def _on_item_clicked(self, item):
        if item is not None:
            self.object_selected.emit(item.text())