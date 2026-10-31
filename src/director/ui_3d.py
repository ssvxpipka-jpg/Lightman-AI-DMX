"""Lightman 3D stage view built on pyqtgraph.opengl."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

import pyqtgraph.opengl as gl


SCENE_PATH = Path("data/scene.json")

FIXTURE_GREY = (0.133, 0.133, 0.133, 1.0)   # #222222 dark grey
FIXTURE_METAL = (0.25, 0.25, 0.28, 1.0)
BEAM_COLOR = (0.3, 0.6, 1.0, 0.3)            # translucent blue
BEAM_LENGTH = 10.0
BEAM_R_TOP = 0.1
BEAM_R_BOTTOM = 2.0


class Lightman3DView(gl.GLViewWidget):
    """3D stage view for Lightman fixtures.

    Native GLViewWidget interaction is active by default:
    left-drag rotates the camera, wheel zooms in and out.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # Camera: 30 units back, 30° up, 45° sideways.
        # Mouse drag (rotate) and wheel (zoom) are GLViewWidget defaults.
        self.setCameraPosition(distance=30, elevation=30, azimuth=45)
        self.setBackgroundColor(QColor(15, 15, 20))
        self.setMinimumSize(420, 320)

        self._scene_data: dict = {"fixtures": []}
        self._meshes_by_id: dict[int, list] = {}
        self._next_id: int = 0

        self._add_floor()

        if SCENE_PATH.exists():
            self.load_scene_state()

    # ------------------------------------------------------------------
    # Floor
    # ------------------------------------------------------------------

    def _add_floor(self) -> None:
        grid = gl.GLGridItem()
        grid.setSize(30, 30)
        grid.setSpacing(1, 1)
        grid.setColor(QColor(60, 60, 75))
        self.addItem(grid)

    # ------------------------------------------------------------------
    # Primitive builders
    # ------------------------------------------------------------------

    def _make_box(self, size, color, x, y, z):
        """Solid box centred at (x, y, z)."""
        item = gl.GLBoxItem()
        item.setSize(float(size[0]), float(size[1]), float(size[2]))
        r, g, b, a = color
        item.setColor(QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255)))
        item.translate(float(x), float(y), float(z))
        return item

    def _make_cylinder(self, radius, length, color, x, y, z):
        """Vertical cylinder centred at (x, y, z), aligned with Z axis."""
        md = gl.MeshData.cylinder(
            rows=8,
            cols=24,
            radius=[float(radius), float(radius)],
            length=float(length),
        )
        item = gl.GLMeshItem(
            meshdata=md,
            smooth=True,
            color=color,
            shader="shaded",
        )
        item.translate(float(x), float(y), float(z))
        return item

    def _make_beam(self, x, y, z_top):
        """Translucent downward-pointing cone (fixture beam).

        MeshData.cone builds a cone opening along +local Z from its narrow
        pole (z = 0, top radius) to its base (z = length, bottom radius).
        The vertexes are flipped so the cone opens downward (-Z), then the
        narrow pole is placed exactly at the fixture head position.
        """
        md = gl.MeshData.cone(
            rows=8,
            cols=32,
            radius=[BEAM_R_TOP, BEAM_R_BOTTOM],
            length=BEAM_LENGTH,
        )
        verts = md.vertexes()
        verts[:, 2] = -verts[:, 2]
        md.setVertexes(verts)
        item = gl.GLMeshItem(
            meshdata=md,
            smooth=True,
            color=BEAM_COLOR,
            shader="shaded",
        )
        item.setGLOptions("additive")
        item.translate(float(x), float(y), float(z_top))
        return item
    def _build_moving_head(self, x, y, z):
        """Moving head: base box, U-shaped yoke (3 thin boxes), head cylinder."""
        parts = []
        # Base
        parts.append(self._make_box((0.7, 0.7, 0.4), FIXTURE_GREY, x, y, z + 0.2))
        # U-shaped yoke: bottom spine + two vertical arms
        parts.append(self._make_box((0.75, 0.1, 0.1), FIXTURE_GREY, x, y, z + 0.45))
        parts.append(self._make_box((0.1, 0.1, 1.0), FIXTURE_GREY, x - 0.325, y, z + 1.0))
        parts.append(self._make_box((0.1, 0.1, 1.0), FIXTURE_GREY, x + 0.325, y, z + 1.0))
        # Head, cradled between the yoke arms
        parts.append(self._make_cylinder(0.16, 0.55, FIXTURE_GREY, x, y, z + 1.175))
        return parts

    def _build_led_bar(self, x, y, z):
        """LED bar: long thin box (2.0 x 0.1 x 0.1)."""
        return [
            self._make_box((2.0, 0.1, 0.1), FIXTURE_GREY, x, y, z + 0.05),
        ]

    def _build_truss(self, x, y, z):
        """Truss: wireframe box (GLBoxItem in line mode)."""
        item = gl.GLBoxItem(mode="lines")
        item.setSize(0.5, 0.5, 2.5)
        item.setColor(QColor(int(FIXTURE_METAL[0] * 255),
                             int(FIXTURE_METAL[1] * 255),
                             int(FIXTURE_METAL[2] * 255),
                             int(FIXTURE_METAL[3] * 255)))
        item.translate(float(x), float(y), float(z) + 1.25)
        return [item]

    def _build_stand(self, x, y, z):
        """Stand: vertical cylinder with base plate and top mount."""
        parts = []
        # Base plate
        parts.append(self._make_box((0.4, 0.4, 0.05), FIXTURE_GREY, x, y, z + 0.025))
        # Vertical pole
        parts.append(self._make_cylinder(0.04, 2.0, FIXTURE_METAL, x, y, z + 1.025))
        # Top mount
        parts.append(self._make_box((0.15, 0.15, 0.1), FIXTURE_GREY, x, y, z + 2.05))
        return parts

    def _build_curtain(self, x, y, z):
        """Curtain: large flat box."""
        return [
            self._make_box((6.0, 0.05, 4.0), (0.05, 0.05, 0.1, 1.0), x, y, z + 2.0),
        ]

    def _build_generic(self, x, y, z):
        return [self._make_box((0.5, 0.5, 0.5), FIXTURE_GREY, x, y, z + 0.25)]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def spawn_fixture_on_stage(self, data: dict) -> int:
        """Spawn a fixture on the stage and return its internal id.

        Reads data['type'] and data['position']; every spawned fixture is
        recorded in self._scene_data["fixtures"].
        """
        if not isinstance(data, dict):
            raise TypeError(
                f"spawn_fixture_on_stage expects dict, got {type(data).__name__}"
            )

        fid = self._next_id
        self._next_id += 1

        pos = data.get("position") or [0, 0, 0]
        if len(pos) < 3:
            pos = list(pos) + [0.0] * (3 - len(pos))
        x, y, z = float(pos[0]), float(pos[1]), float(pos[2])

        ftype = (data.get("type") or "").lower()

        if ftype == "moving_head" or ("moving" in ftype and "head" in ftype):
            parts = self._build_moving_head(x, y, z)
            # Translucent beam pointing downward from the fixture head.
            parts.append(self._make_beam(x, y, z + 1.45))
        elif ftype == "led_bar" or ("led" in ftype and "bar" in ftype):
            parts = self._build_led_bar(x, y, z)
            parts.append(self._make_beam(x, y, z + 0.1))
        elif ftype == "truss" or "truss" in ftype:
            parts = self._build_truss(x, y, z)
        elif ftype == "stand" or "stand" in ftype:
            parts = self._build_stand(x, y, z)
        elif ftype == "curtain" or "curtain" in ftype:
            parts = self._build_curtain(x, y, z)
        else:
            parts = self._build_generic(x, y, z)

        for p in parts:
            self.addItem(p)

        stored = dict(data)
        stored["_id"] = fid
        stored["position"] = [x, y, z]
        self._scene_data["fixtures"].append(stored)
        self._meshes_by_id[fid] = parts
        return fid

    def delete_scene(self) -> None:
        for parts in list(self._meshes_by_id.values()):
            for item in parts:
                self.removeItem(item)
        self._meshes_by_id.clear()
        self._scene_data = {"fixtures": []}
        self._next_id = 0

    def save_scene_state(self) -> None:
        SCENE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCENE_PATH.write_text(
            json.dumps(self._scene_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_scene_state(self) -> None:
        if not SCENE_PATH.exists():
            return
        raw = json.loads(SCENE_PATH.read_text(encoding="utf-8"))
        self.delete_scene()
        for fixture in raw.get("fixtures", []):
            cleaned = {k: v for k, v in fixture.items() if k != "_id"}
            self.spawn_fixture_on_stage(cleaned)

    def get_stage_fixtures(self) -> list:
        return [dict(f) for f in self._scene_data.get("fixtures", [])]

    @property
    def fixtures(self) -> list:
        return self._scene_data.get("fixtures", [])

