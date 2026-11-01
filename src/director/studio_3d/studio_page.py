"""
Studio 3D page — toolbar, library, viewport, objects+properties.

Handles:
    - mounting (truss/stand active, attach fixtures, Move here)
    - dead zones
    - Add Model (.obj / .glb / .gltf)
    - Select / Eraser tools
    - Blackout / Resume state
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QPushButton, QLabel, QFileDialog, QMessageBox,
)

from src.director.ui_3d import Lightman3DView
from src.director.studio_3d.panels.fixture_library import (
    FixtureLibraryPanel, _load_catalogue, _HARDCODED,
)
from src.director.studio_3d.panels.scene_objects_panel import SceneObjectsPanel
from src.director.studio_3d.panels.properties_panel import PropertiesPanel


_LIGHT_TYPES = {
    "moving_head", "movinghead", "moving head", "moving heads",
    "led_bar", "ledbar", "led bar", "led bars", "led",
    "laser", "lasers", "strobe", "strobes", "dimmer", "dimmers",
}


def _is_light(data):
    return str(data.get("type", "")).lower().strip() in _LIGHT_TYPES


def _find_fixture_by_name(name):
    target = (name or "").strip().lower()
    if not target:
        return None
    for fx in _load_catalogue():
        if str(fx.get("name", "")).strip().lower() == target:
            return fx
    for items in _HARDCODED.values():
        for fx in items:
            if str(fx.get("name", "")).strip().lower() == target:
                return fx
    return None


class Studio3DPage(QWidget):
    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.mounts = []
        self.dead_zones = []
        self.active_mount = None
        self.blackout_active = False
        self.saved_intensities = {}

        # ---- Toolbar ----
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        a_add = QAction("➕ Add Model", self)
        a_add.triggered.connect(self._on_add_model)
        self.toolbar.addAction(a_add)

        a_load = QAction("Load Room", self)
        a_load.triggered.connect(self._on_load_room)
        self.toolbar.addAction(a_load)

        a_save = QAction("Save Scene", self)
        a_save.triggered.connect(self._on_save_scene)
        self.toolbar.addAction(a_save)

        a_clear = QAction("Clear Scene", self)
        a_clear.triggered.connect(self._on_clear_scene)
        self.toolbar.addAction(a_clear)

        self.toolbar.addSeparator()

        self.action_select = QAction("Select", self)
        self.action_select.setCheckable(True)
        self.action_select.setChecked(True)
        self.action_select.triggered.connect(self._on_tool_select)
        self.toolbar.addAction(self.action_select)

        self.action_eraser = QAction("Eraser", self)
        self.action_eraser.setCheckable(True)
        self.action_eraser.triggered.connect(self._on_tool_eraser)
        self.toolbar.addAction(self.action_eraser)

        self.toolbar.addSeparator()

        self.action_blackout = QAction("⬛ Blackout", self)
        self.action_blackout.setShortcut("Escape")
        self.action_blackout.triggered.connect(self._on_blackout)
        self.toolbar.addAction(self.action_blackout)

        self.action_resume = QAction("▶ Resume", self)
        self.action_resume.triggered.connect(self._on_resume)
        self.toolbar.addAction(self.action_resume)

        # ---- Panels ----
        self.fixture_library = FixtureLibraryPanel()
        self.view_3d = Lightman3DView()
        self.scene_objects_panel = SceneObjectsPanel()
        self.properties_panel = PropertiesPanel()
        self.fixture_library.setFixedWidth(250)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(4)
        rl.addWidget(self.scene_objects_panel, 1)
        rl.addWidget(self.properties_panel, 1)
        right.setFixedWidth(250)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.fixture_library)
        splitter.addWidget(self.view_3d)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)

        # ---- Bottom bar ----
        bottom = QWidget()
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(8, 6, 8, 6)
        self.start_btn = QPushButton("Start")
        self.record_btn = QPushButton("Record")
        self.stop_btn = QPushButton("Stop")
        self.bpm_label = QLabel("BPM: —")
        self.energy_label = QLabel("Energy: —")
        bl.addWidget(self.start_btn)
        bl.addWidget(self.record_btn)
        bl.addWidget(self.stop_btn)
        bl.addStretch(1)
        bl.addWidget(self.bpm_label)
        bl.addSpacing(16)
        bl.addWidget(self.energy_label)

        # ---- Root ----
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(splitter, 1)
        layout.addWidget(bottom)

        # ---- Connections ----
        self.fixture_library.fixture_selected.connect(self._on_library_click)
        self.scene_objects_panel.object_removed.connect(self.remove_fixture_by_name)
        self.scene_objects_panel.object_selected.connect(self._on_object_selected)
        self.properties_panel.attach_requested.connect(self._on_attach_requested)
        self.view_3d.on_fixture_selected = self._on_object_selected

    # ============================================================ public

    def spawn_fixture(self, data):
        if not isinstance(data, dict):
            return
        if self.blackout_active:
            self.log_message.emit("⚠ Blackout active — spawn ignored")
            return
        if data.get("is_zone"):
            self._spawn_dead_zone(data)
            return
        if data.get("is_mount"):
            self._spawn_mount(data)
            return
        payload = dict(data)
        if _is_light(data) and self.active_mount is not None:
            payload = self._attached_payload(payload, self.active_mount)
            note = f"→ attached to {self.active_mount.get('name')}"
        elif _is_light(data):
            note = "⚠ on ground (select a mount first)"
        else:
            note = ""
        try:
            self.view_3d.spawn_fixture_on_stage(payload)
        except Exception as exc:
            self.log_message.emit(f"Spawn failed: {exc}")
            return
        name = payload.get("name") or payload.get("type") or "Fixture"
        self.scene_objects_panel.add_object(name, kind="fixture")
        self.log_message.emit(f"Spawned: {name} {note}".strip())

    def spawn_fixture_by_name(self, name):
        if self.blackout_active:
            self.log_message.emit(
                "⚠ Blackout active — AI spawn ignored")
            return
        fx = _find_fixture_by_name(name)
        if fx is None:
            self.log_message.emit(f"AI tried to spawn '{name}' — not found.")
            return
        self.spawn_fixture(fx)

    def remove_fixture_by_name(self, name):
        target = (name or "").strip()
        if not target:
            return
        for m in list(self.mounts):
            if m.get("name") == target:
                self.mounts.remove(m)
                if self.active_mount and self.active_mount.get("name") == target:
                    self.active_mount = None
                self._refresh_mounts_in_properties()
                break
        for z in list(self.dead_zones):
            if z.get("name") == target:
                self.dead_zones.remove(z)
                break
        self.view_3d.remove_fixture_by_name(target)
        self.scene_objects_panel.remove_object(target)
        self.properties_panel.set_fixture({})
        self.log_message.emit(f"Removed: {target}")

    def get_dead_zones(self):
        return list(self.dead_zones)

    # ---------------------------------------------------- blackout

    def enter_blackout(self):
        if self.blackout_active:
            return
        self.saved_intensities = {}
        for fx in self.view_3d.fixtures:
            if fx.get("is_mount") or fx.get("is_zone"):
                continue
            if fx.get("is_work_light"):
                continue
            self.saved_intensities[fx.get("name")] = int(fx.get("intensity", 100))

        self.view_3d.apply_blackout()

        if not self.view_3d.verify_blackout():
            self.log_message.emit(
                "[BLACKOUT] ERROR: some fixtures stuck. Lock NOT engaged.")
            return False

        self.blackout_active = True
        self.log_message.emit("[BLACKOUT] LOCKED. All controls frozen.")
        return True

    def exit_blackout(self):
        if not self.blackout_active:
            return
        self.view_3d.restore_intensities(self.saved_intensities)
        self.saved_intensities = {}
        self.blackout_active = False
        self.log_message.emit("[RESUME] LOCK released. Show restored.")

    # ============================================================ internal

    def _attached_payload(self, fixture, mount):
        mpos = mount.get("position", [0.0, 0.0, 0.0])
        mheight = float(mount.get("height", 0.0))
        payload = dict(fixture)
        payload["position"] = [
            float(mpos[0]), float(mpos[1]) + mheight, float(mpos[2]),
        ]
        payload["attached_to"] = mount.get("name")
        return payload

    def _spawn_mount(self, data):
        try:
            self.view_3d.spawn_fixture_on_stage(data)
        except Exception as exc:
            self.log_message.emit(f"Mount spawn failed: {exc}")
            return
        self.mounts.append(data)
        self.active_mount = data
        self.scene_objects_panel.add_object(data.get("name", "Mount"), kind="mount")
        self._refresh_mounts_in_properties()
        self.log_message.emit(f"Mount placed & active: {data.get('name')}")

    def _spawn_dead_zone(self, data):
        try:
            self.view_3d.spawn_fixture_on_stage(data)
        except Exception as exc:
            self.log_message.emit(f"Dead zone spawn failed: {exc}")
            return
        self.dead_zones.append(data)
        self.scene_objects_panel.add_object(data.get("name", "Zone"), kind="zone")
        self.log_message.emit(f"Dead zone added: {data.get('name')}")

    def _refresh_mounts_in_properties(self):
        self.properties_panel.set_mounts(self.mounts)

    # ============================================================ slots

    def _on_library_click(self, data):
        if not isinstance(data, dict):
            return
        if data.get("is_mount"):
            self._spawn_mount(data)
        elif data.get("is_zone"):
            self._spawn_dead_zone(data)
        else:
            self.spawn_fixture(data)

    def _on_object_selected(self, name):
        for fx in list(self.view_3d.fixtures):
            label = fx.get("name") or fx.get("type") or ""
            if label == name:
                self.properties_panel.set_fixture(fx)
                if fx.get("is_mount"):
                    self.active_mount = fx
                    self.log_message.emit(f"Active mount: {name}")
                return
        for m in self.mounts:
            if m.get("name") == name:
                self.properties_panel.set_fixture(m)
                self.active_mount = m
                self.log_message.emit(f"Active mount: {name}")
                return
        for z in self.dead_zones:
            if z.get("name") == name:
                self.properties_panel.set_fixture(z)
                return
        self.properties_panel.set_fixture({})

    def _on_attach_requested(self, fixture_name, mount_name):
        target = next(
            (m for m in self.mounts if m.get("name") == mount_name), None
        )
        if target is None:
            self.log_message.emit(f"Move failed: mount '{mount_name}' not found.")
            return
        current = None
        for fx in list(self.view_3d.fixtures):
            if fx.get("name") == fixture_name:
                current = dict(fx)
                break
        if current is None:
            self.log_message.emit(
                f"Move failed: fixture '{fixture_name}' not found.")
            return
        self.view_3d.remove_fixture_by_name(fixture_name)
        new_payload = self._attached_payload(current, target)
        try:
            self.view_3d.spawn_fixture_on_stage(new_payload)
        except Exception as exc:
            self.log_message.emit(f"Move failed: {exc}")
            return
        self.properties_panel.set_fixture(new_payload)
        self.log_message.emit(f"Moved: {fixture_name} → {mount_name}")

    def _on_blackout(self):
        if self.enter_blackout():
            self.action_blackout.setEnabled(False)
            self.action_resume.setEnabled(True)

    def _on_resume(self):
        self.exit_blackout()
        self.action_blackout.setEnabled(True)
        self.action_resume.setEnabled(False)

    def _on_tool_select(self):
        if not self.action_select.isChecked():
            self.action_select.setChecked(True)
            return
        self.action_eraser.setChecked(False)
        self.view_3d.set_tool("select")
        self.log_message.emit("Tool: Select")

    def _on_tool_eraser(self):
        if not self.action_eraser.isChecked():
            self.action_eraser.setChecked(True)
            return
        self.action_select.setChecked(False)
        self.view_3d.set_tool("eraser")
        self.log_message.emit("Tool: Eraser")

    def _on_add_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Add 3D Model", "",
            "3D Models (*.obj *.glb *.gltf);;All Files (*)",
        )
        if not path:
            return
        try:
            self.view_3d.load_room_model(path)
        except Exception as exc:
            self.log_message.emit(f"Model load failed: {exc}")
            return
        name = os.path.basename(path)
        self.scene_objects_panel.add_object(name, kind="model")
        self.log_message.emit(f"Model added: {name}")

    def _on_load_room(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Room", "", "OBJ Files (*.obj)"
        )
        if not path:
            return
        try:
            self.view_3d.load_room_model(path)
        except Exception as exc:
            self.log_message.emit(f"Room load failed: {exc}")
            return
        self.log_message.emit(f"Room loaded: {os.path.basename(path)}")

    def _on_save_scene(self):
        try:
            self.view_3d.save_scene()
            self.log_message.emit("Scene saved.")
        except Exception as exc:
            self.log_message.emit(f"Save failed: {exc}")

    def _on_clear_scene(self):
        self.view_3d.clear_scene()
        self.mounts.clear()
        self.dead_zones.clear()
        self.active_mount = None
        self.scene_objects_panel.clear()
        self.properties_panel.set_fixture({})
        self._refresh_mounts_in_properties()
        self.log_message.emit("Scene cleared.")