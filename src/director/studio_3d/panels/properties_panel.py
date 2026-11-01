"""
Properties panel — shows the selected object and, for lights, offers
a dropdown to re-attach the fixture to any spawned mount (truss/stand).
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QComboBox, QPushButton,
    QHBoxLayout, QGroupBox,
)

_LIGHT_TYPES = {
    "moving_head", "movinghead", "moving head", "moving heads",
    "led_bar", "ledbar", "led bar", "led bars", "led",
    "laser", "lasers", "strobe", "strobes", "dimmer", "dimmers",
}


def _is_light(data: dict) -> bool:
    return str(data.get("type", "")).lower().strip() in _LIGHT_TYPES


class PropertiesPanel(QWidget):
    attach_requested = Signal(str, str)  # fixture_name, mount_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self._current = {}
        self._mounts = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Properties")
        title.setObjectName("Section")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)
        self.name_value = QLabel("—")
        self.type_value = QLabel("—")
        self.position_value = QLabel("—")
        self.beam_value = QLabel("—")
        self.attached_value = QLabel("—")
        form.addRow("Name:", self.name_value)
        form.addRow("Type:", self.type_value)
        form.addRow("Position:", self.position_value)
        form.addRow("Beam Angle:", self.beam_value)
        form.addRow("Attached to:", self.attached_value)
        layout.addLayout(form)

        # ---- Attach group (only visible for lights) ----
        self.attach_group = QGroupBox("Attach to mount")
        ag_layout = QVBoxLayout(self.attach_group)
        ag_layout.setSpacing(6)

        self.mount_combo = QComboBox()
        ag_layout.addWidget(self.mount_combo)

        btn_row = QHBoxLayout()
        self.move_btn = QPushButton("Move here")
        self.move_btn.setObjectName("Primary")
        self.move_btn.clicked.connect(self._on_move)
        btn_row.addWidget(self.move_btn)
        btn_row.addStretch(1)
        ag_layout.addLayout(btn_row)

        self.attach_group.setVisible(False)
        layout.addWidget(self.attach_group)
        layout.addStretch(1)

    # -------------------------------------------------------------- public

    def set_fixture(self, data: dict):
        self._current = dict(data) if data else {}
        self._refresh()

    def set_mounts(self, mounts: list):
        self._mounts = list(mounts or [])
        self.mount_combo.clear()
        for m in self._mounts:
            self.mount_combo.addItem(m.get("name", "Mount"), m.get("name", ""))
        # Restore selection if current fixture is attached to something
        attached = self._current.get("attached_to")
        if attached:
            idx = self.mount_combo.findData(attached)
            if idx >= 0:
                self.mount_combo.setCurrentIndex(idx)
        self._refresh()

    # -------------------------------------------------------------- private

    def _refresh(self):
        data = self._current
        if not data:
            self.name_value.setText("—")
            self.type_value.setText("—")
            self.position_value.setText("—")
            self.beam_value.setText("—")
            self.attached_value.setText("—")
            self.attach_group.setVisible(False)
            return

        self.name_value.setText(str(data.get("name", "—")))
        self.type_value.setText(str(data.get("type", "—")))

        pos = data.get("position") or (
            data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0)
        )
        try:
            self.position_value.setText(
                f"({float(pos[0]):.2f}, {float(pos[1]):.2f}, {float(pos[2]):.2f})"
            )
        except (TypeError, ValueError, IndexError):
            self.position_value.setText("—")

        beam = data.get("beam_angle", data.get("beamAngle"))
        self.beam_value.setText(
            f"{float(beam):.1f}°" if beam is not None else "—"
        )

        self.attached_value.setText(str(data.get("attached_to") or "—"))

        # Show attach UI only for light fixtures and when mounts exist
        show = _is_light(data) and bool(self._mounts)
        self.attach_group.setVisible(show)

    def _on_move(self):
        if not self._current:
            return
        fixture_name = self._current.get("name", "")
        mount_name = self.mount_combo.currentData()
        if not fixture_name or not mount_name:
            return
        self.attach_requested.emit(fixture_name, mount_name)