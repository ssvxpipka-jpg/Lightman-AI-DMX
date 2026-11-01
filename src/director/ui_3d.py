"""
Lightman 3D view — OpenGL viewport.

Renders fixtures, mounts, dead zones. Supports per-fixture intensity
(0–100) which drives mesh opacity in 3D and will drive real DMX later.

Public API:
    fixtures (property)
    spawn_fixture_on_stage(data) -> id
    remove_fixture_by_name(name)
    clear_scene()
    set_tool(name)
    set_intensity(name, value)   # 0–100
    get_intensity(name) -> int
    apply_blackout()
    verify_blackout() -> bool
    restore_intensities(saved: dict)
    load_room_model(filepath)
    save_scene()
    load_scene_state()
"""

import json
import os

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from pyqtgraph.opengl import MeshData

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


# ===========================================================================
# Geometry helpers
# ===========================================================================

def _make_box(sx, sy, sz):
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    verts = np.array([
        [-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz],
        [-hx, -hy,  hz], [hx, -hy,  hz], [hx, hy,  hz], [-hx, hy,  hz],
    ], dtype=float)
    faces = np.array([
        [0, 1, 2], [0, 2, 3],
        [4, 6, 5], [4, 7, 6],
        [0, 4, 5], [0, 5, 1],
        [3, 2, 6], [3, 6, 7],
        [0, 3, 7], [0, 7, 4],
        [1, 5, 6], [1, 6, 2],
    ], dtype=int)
    return verts, faces


def _make_box_edges(sx, sy, sz):
    hx, hy, hz = sz / 2.0, sy, sx / 2.0
    corners = np.array([
        [-hx, 0, -hz], [hx, 0, -hz], [hx, 0, hz], [-hx, 0, hz],
        [-hx, hy, -hz], [hx, hy, -hz], [hx, hy, hz], [-hx, hy, hz],
    ], dtype=float)
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    pts = []
    for a, b in edges:
        pts.append(corners[a])
        pts.append(corners[b])
    return np.array(pts, dtype=float)


def _make_cylinder(radius, height, segments=20):
    verts = []
    for i in range(segments):
        angle = 2.0 * np.pi * i / segments
        verts.append([radius * np.cos(angle), 0.0, radius * np.sin(angle)])
    for i in range(segments):
        angle = 2.0 * np.pi * i / segments
        verts.append([radius * np.cos(angle), height, radius * np.sin(angle)])
    verts.append([0.0, 0.0, 0.0])
    verts.append([0.0, height, 0.0])
    bot_c = 2 * segments
    top_c = 2 * segments + 1
    faces = []
    for i in range(segments):
        a = i
        b = (i + 1) % segments
        ta = segments + a
        tb = segments + b
        faces.append([a, ta, tb])
        faces.append([a, tb, b])
        faces.append([bot_c, b, a])
        faces.append([top_c, ta, tb])
    return np.array(verts, dtype=float), np.array(faces, dtype=int)


def _make_beam_cone(radius_top, radius_bottom, length, segments=20):
    verts = []
    for i in range(segments):
        angle = 2.0 * np.pi * i / segments
        verts.append([radius_top * np.cos(angle), 0.0, radius_top * np.sin(angle)])
    for i in range(segments):
        angle = 2.0 * np.pi * i / segments
        verts.append([radius_bottom * np.cos(angle), -length,
                      radius_bottom * np.sin(angle)])
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append([i, j, segments + j])
        faces.append([i, segments + j, segments + i])
    return np.array(verts, dtype=float), np.array(faces, dtype=int)


def _with_alpha(color, alpha):
    return (color[0], color[1], color[2], max(0.0, min(1.0, alpha)))


# ===========================================================================
# Lightman3DView
# ===========================================================================

class Lightman3DView(gl.GLViewWidget):

    BODY_COLOR = {
        "moving_head": (0.25, 0.25, 0.30, 1.0),
        "laser":       (0.15, 0.15, 0.15, 1.0),
        "strobe":      (0.35, 0.35, 0.35, 1.0),
        "led_bar":     (0.20, 0.20, 0.20, 1.0),
        "dimmer":      (0.25, 0.25, 0.25, 1.0),
    }
    BEAM_COLOR = {
        "moving_head": (1.0, 0.9, 0.6, 0.25),
        "laser":       (1.0, 0.1, 0.1, 0.45),
        "strobe":      (1.0, 1.0, 1.0, 0.35),
        "led_bar":     (0.55, 0.8, 1.0, 0.20),
        "dimmer":      (1.0, 0.8, 0.5, 0.20),
    }
    BODY_SIZE = {
        "moving_head": (0.30, 0.45, 0.30),
        "led_bar":     (1.40, 0.12, 0.12),
        "laser":       (0.20, 0.20, 0.20),
        "strobe":      (0.30, 0.20, 0.30),
        "dimmer":      (0.20, 0.15, 0.20),
    }
    BEAM_RADIUS = {
        "moving_head": 1.5, "laser": 0.8, "strobe": 1.0,
        "dimmer": 1.0, "led_bar": 2.0,
    }
    BEAM_LENGTH = {
        "moving_head": 8.0, "laser": 10.0, "strobe": 5.0,
        "dimmer": 4.0, "led_bar": 6.0,
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self._next_id = 0
        self._meshes_by_id = {}
        self._scene_data = {
            "fixtures": [],
            "dead_zones": [],
            "room_bounds": None,
        }
        self.current_tool = "select"
        self.on_fixture_selected = None
        self._press_pos = None
        self._press_moved = False
        self._room_item = None

        self.setBackgroundColor(QColor(23, 23, 23))
        self.opts["distance"] = 18
        self.opts["elevation"] = 25
        self.opts["azimuth"] = 45
        self.opts["fov"] = 60
        self.setMinimumSize(400, 300)

        grid = gl.GLGridItem()
        grid.setSize(20, 20)
        grid.setSpacing(1, 1)
        grid.setColor((90, 90, 90, 80))
        self.addItem(grid)

    # ============================================================ public

    @property
    def fixtures(self):
        return self._scene_data.get("fixtures", [])

    def set_tool(self, tool_name):
        self.current_tool = tool_name

    def spawn_fixture_on_stage(self, data):
        if not isinstance(data, dict):
            return 0
        pos = data.get("position", [0.0, 0.0, 0.0])
        try:
            x, y, z = float(pos[0]), float(pos[1]), float(pos[2])
        except (TypeError, ValueError, IndexError):
            x, y, z = 0.0, 0.0, 0.0

        if data.get("is_zone"):
            return self._spawn_zone(data, x, y, z)
        if data.get("is_mount"):
            return self._spawn_mount(data, x, y, z)
        return self._spawn_fixture(data, x, y, z)

    def remove_fixture_by_name(self, name):
        name = (name or "").strip()
        if not name:
            return
        for i, zone in enumerate(self._scene_data["dead_zones"]):
            if (zone.get("name") or "").strip() == name:
                for item in zone.get("_items", []):
                    self.removeItem(item)
                self._meshes_by_id.pop(zone.get("_id"), None)
                self._scene_data["dead_zones"].pop(i)
                return
        for i, fx in enumerate(self._scene_data["fixtures"]):
            if (fx.get("name") or fx.get("type") or "").strip() == name:
                for item in fx.get("_items", []):
                    self.removeItem(item)
                self._meshes_by_id.pop(fx.get("_id"), None)
                self._scene_data["fixtures"].pop(i)
                return

    def clear_scene(self):
        for items in list(self._meshes_by_id.values()):
            for item in items:
                self.removeItem(item)
        self._meshes_by_id.clear()
        self._scene_data["fixtures"] = []
        self._scene_data["dead_zones"] = []
        self._next_id = 0

    # --------------------------------------------------- intensity / blackout

    def set_intensity(self, name, value):
        """Set fixture intensity 0–100. Updates visual opacity of meshes."""
        name = (name or "").strip()
        try:
            value = max(0, min(100, int(value)))
        except (TypeError, ValueError):
            return

        for fx in self._scene_data["fixtures"]:
            if (fx.get("name") or "").strip() == name:
                fx["intensity"] = value
                self._apply_visual_intensity(fx, value)
                return

    def get_intensity(self, name):
        name = (name or "").strip()
        for fx in self._scene_data["fixtures"]:
            if (fx.get("name") or "").strip() == name:
                return int(fx.get("intensity", 100))
        return 0

    def apply_blackout(self):
        """Show fixtures → 0%, work light → default_intensity (usually 2%)."""
        for fx in self._scene_data["fixtures"]:
            if fx.get("is_mount") or fx.get("is_zone"):
                continue
            if fx.get("is_work_light"):
                target = int(fx.get("default_intensity", 2))
            else:
                target = 0
            fx["intensity"] = target
            self._apply_visual_intensity(fx, target)

    def verify_blackout(self):
        """Return True if every non-work-light fixture has intensity == 0."""
        for fx in self._scene_data["fixtures"]:
            if fx.get("is_mount") or fx.get("is_zone"):
                continue
            if fx.get("is_work_light"):
                continue
            if int(fx.get("intensity", 100)) != 0:
                return False
        return True

    def restore_intensities(self, saved):
        """Restore previously saved intensities. Work light goes to 0."""
        for fx in self._scene_data["fixtures"]:
            if fx.get("is_mount") or fx.get("is_zone"):
                continue
            name = fx.get("name")
            if fx.get("is_work_light"):
                target = 0
            else:
                target = int(saved.get(name, 100))
            fx["intensity"] = target
            self._apply_visual_intensity(fx, target)

    def _apply_visual_intensity(self, fx, value):
        """Adjust mesh visibility based on intensity.

        Body meshes: alpha scales from 0.15 (dark) to 1.0 (bright).
        Beam meshes: alpha scales from 0.0 (invisible) to original beam alpha.
        """
        body_items = fx.get("_body_items", [])
        beam_items = fx.get("_beam_items", [])
        body_base = fx.get("_body_color", (0.3, 0.3, 0.3, 1.0))
        beam_base = fx.get("_beam_color", (1.0, 1.0, 1.0, 0.3))

        t = max(0.0, min(1.0, value / 100.0))
        body_alpha = 0.15 + 0.85 * t
        beam_alpha = beam_base[3] * t

        for item in body_items:
            try:
                item.setColor(_with_alpha(body_base, body_alpha))
            except Exception:
                pass

        for item in beam_items:
            try:
                item.setColor(_with_alpha(beam_base, beam_alpha))
                item.setVisible(value > 0)
            except Exception:
                pass

    # ------------------------------------------------------------- room/scene

    def load_room_model(self, filepath):
        if not os.path.isfile(filepath):
            raise FileNotFoundError(filepath)
        from src.director.studio_3d.tools.scene_tools import SceneTools
        item = SceneTools.load_obj(filepath)
        self.addItem(item)
        self._room_item = item

        verts = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("v "):
                    parts = line.split()
                    verts.append([float(parts[1]), float(parts[2]), float(parts[3])])

        if verts:
            arr = np.array(verts)
            self._scene_data["room_bounds"] = {
                "min": arr.min(axis=0).tolist(),
                "max": arr.max(axis=0).tolist(),
                "filepath": filepath,
            }
        else:
            self._scene_data["room_bounds"] = None

    def save_scene(self):
        def _strip(items):
            out = []
            for fx in items:
                clean = {k: v for k, v in fx.items() if not k.startswith("_")}
                out.append(clean)
            return out
        path = os.path.join(_PROJECT_ROOT, "data", "scene.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fixtures": _strip(self._scene_data["fixtures"]),
                    "dead_zones": _strip(self._scene_data["dead_zones"]),
                },
                f, indent=2,
            )

    def load_scene_state(self):
        path = os.path.join(_PROJECT_ROOT, "data", "scene.json")
        if not os.path.isfile(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for fx in data.get("fixtures", []):
            self.spawn_fixture_on_stage(fx)
        for zone in data.get("dead_zones", []):
            self.spawn_fixture_on_stage(zone)

    # ------------------------------------------------------------- spawn

    def _spawn_zone(self, data, x, y, z):
        size = data.get("size", [2.0, 2.0, 2.0])
        try:
            sx, sy, sz = float(size[0]), float(size[1]), float(size[2])
        except (TypeError, ValueError, IndexError):
            sx, sy, sz = 2.0, 2.0, 2.0
        edges = _make_box_edges(sx, sy, sz)
        item = gl.GLLinePlotItem(
            pos=edges, color=(1.0, 0.15, 0.15, 1.0),
            width=2, mode="lines", antialias=True,
        )
        item.translate(x - sx / 2.0, y, z - sz / 2.0)
        self.addItem(item)

        zone = dict(data)
        zone["_id"] = self._next_id
        zone["_items"] = [item]
        self._next_id += 1
        self._scene_data["dead_zones"].append(zone)
        self._meshes_by_id[zone["_id"]] = [item]
        return zone["_id"]

    def _spawn_mount(self, data, x, y, z):
        ftype = str(data.get("type", "")).lower()
        if ftype == "truss":
            length = float(data.get("length", 2.0))
            height = float(data.get("height", 0.3))
            width = float(data.get("width", 0.3))
            edges = _make_box_edges(length, height, width)
            item = gl.GLLinePlotItem(
                pos=edges, color=(0.9, 0.9, 0.9, 1.0),
                width=2, mode="lines", antialias=True,
            )
            item.translate(x, y, z)
        elif ftype == "stand":
            height = float(data.get("height", 1.0))
            verts, faces = _make_cylinder(0.05, height)
            mesh = MeshData(vertexes=verts, faces=faces)
            item = gl.GLMeshItem(
                meshdata=mesh, smooth=True, drawFaces=True,
                drawEdges=False, color=(0.6, 0.6, 0.65, 1.0),
            )
            item.translate(x, y, z)
        else:
            verts, faces = _make_box(0.5, 0.5, 0.5)
            mesh = MeshData(vertexes=verts, faces=faces)
            item = gl.GLMeshItem(
                meshdata=mesh, smooth=False, drawFaces=True,
                drawEdges=True, edgeColor=(0.1, 0.1, 0.1, 1.0),
                color=(0.6, 0.6, 0.6, 1.0),
            )
            item.translate(x, y, z)
        self.addItem(item)
        mount = dict(data)
        mount["_id"] = self._next_id
        mount["_items"] = [item]
        self._next_id += 1
        self._scene_data["fixtures"].append(mount)
        self._meshes_by_id[mount["_id"]] = [item]
        return mount["_id"]

    def _spawn_fixture(self, data, x, y, z):
        ftype = str(data.get("type", "")).lower()
        items = []
        body_items = []
        beam_items = []
        body_color = self.BODY_COLOR.get(ftype, (0.3, 0.3, 0.3, 1.0))
        beam_color = self.BEAM_COLOR.get(ftype, (1.0, 1.0, 1.0, 0.2))

        if ftype == "curtain":
            width = float(data.get("width", 6.0))
            height = float(data.get("height", 4.0))
            verts = np.array([
                [-width / 2, 0, 0], [width / 2, 0, 0],
                [width / 2, height, 0], [-width / 2, height, 0],
            ], dtype=float)
            faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=int)
            mesh = MeshData(vertexes=verts, faces=faces)
            item = gl.GLMeshItem(
                meshdata=mesh, smooth=False, drawFaces=True,
                drawEdges=False, color=(0.08, 0.08, 0.08, 1.0),
            )
            item.translate(x, y, z)
            self.addItem(item)
            items.append(item)
        else:
            body_size = self.BODY_SIZE.get(ftype, (0.3, 0.3, 0.3))
            verts, faces = _make_box(*body_size)
            mesh = MeshData(vertexes=verts, faces=faces)
            body = gl.GLMeshItem(
                meshdata=mesh, smooth=False, drawFaces=True,
                drawEdges=True, edgeColor=(0.05, 0.05, 0.05, 1.0),
                color=body_color,
            )
            body.translate(x, y + body_size[1] / 2.0, z)
            self.addItem(body)
            items.append(body)
            body_items.append(body)

            if ftype in self.BEAM_RADIUS:
                r_bottom = self.BEAM_RADIUS[ftype]
                length = self.BEAM_LENGTH[ftype]
                verts, faces = _make_beam_cone(0.05, r_bottom, length)
                mesh = MeshData(vertexes=verts, faces=faces)
                beam = gl.GLMeshItem(
                    meshdata=mesh, smooth=True, drawFaces=True,
                    drawEdges=False, color=beam_color,
                )
                beam.translate(x, y + body_size[1], z)
                beam.setGLOptions("additive")
                self.addItem(beam)
                items.append(beam)
                beam_items.append(beam)

        fixture = dict(data)
        fixture["_id"] = self._next_id
        fixture["_items"] = items
        fixture["_body_items"] = body_items
        fixture["_beam_items"] = beam_items
        fixture["_body_color"] = body_color
        fixture["_beam_color"] = beam_color
        if "intensity" not in fixture:
            fixture["intensity"] = int(data.get("intensity", 100))
        if data.get("is_work_light") and "default_intensity" not in fixture:
            fixture["default_intensity"] = 2
        self._next_id += 1
        self._scene_data["fixtures"].append(fixture)
        self._meshes_by_id[fixture["_id"]] = items

        self._apply_visual_intensity(fixture, fixture["intensity"])
        return fixture["_id"]

    # --------------------------------------------------- projection / hit

    def _project(self, x, y, z):
        proj = self.projectionMatrix()
        view = self.viewMatrix()
        if proj is None or view is None:
            return None
        mvp = proj * view
        data = np.array(mvp.data(), dtype=float).reshape(4, 4).T
        v = np.array([x, y, z, 1.0])
        out = data @ v
        if out[3] == 0:
            return None
        ndc = out[:3] / out[3]
        vp = self.getViewport()
        if vp is None:
            return None
        sx = (ndc[0] + 1.0) * 0.5 * vp.width()
        sy = (1.0 - ndc[1]) * 0.5 * vp.height()
        return (sx, sy)

    def _hit_test(self, x, y):
        threshold = 45.0
        best = None
        best_dist = threshold
        all_items = (
            list(self._scene_data["fixtures"])
            + list(self._scene_data["dead_zones"])
        )
        for fx in all_items:
            pos = fx.get("position", [0, 0, 0])
            try:
                px, py, pz = float(pos[0]), float(pos[1]), float(pos[2])
            except (TypeError, ValueError, IndexError):
                continue
            screen = self._project(px, py, pz)
            if screen is None:
                continue
            dx = screen[0] - x
            dy = screen[1] - y
            d = (dx * dx + dy * dy) ** 0.5
            if d < best_dist:
                best_dist = d
                best = fx.get("name")
        return best

    # ------------------------------------------------------------- events

    def mousePressEvent(self, event):
        self._press_pos = event.position()
        self._press_moved = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None:
            moved = (event.position() - self._press_pos).manhattanLength()
            if moved > 5:
                self._press_moved = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._press_pos is None:
            return
        was_click = (not self._press_moved) and event.button() == Qt.LeftButton
        self._press_pos = None
        self._press_moved = False
        if not was_click:
            return
        name = self._hit_test(event.position().x(), event.position().y())
        if not name:
            return
        if self.current_tool == "eraser":
            self.remove_fixture_by_name(name)
        elif self.current_tool == "select":
            if callable(self.on_fixture_selected):
                try:
                    self.on_fixture_selected(name)
                except Exception:
                    pass