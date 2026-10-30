#!/usr/bin/env python3
"""
Lightman 3D Scene View (PySide6 + PyQtGraph OpenGL)
====================================================
Renders stage fixtures using basic primitive geometries (boxes, cylinders)
built from numpy vertex/faces arrays.  No external 3D model files required.

Fixtures:
  - Moving Head: base box + U-shaped yoke + head cylinder + lens cone
  - LED Bar: long thin box
  - Beams: translucent GLLinePlotItem lines with alpha, beam angle from fixture data

Public API:
  - create_moving_head(pos) -> list[GLMeshItem]
  - create_led_bar(pos, rotation) -> GLMeshItem
  - create_beam(start_pos, end_pos, color) -> GLLinePlotItem
  - Lightman3DView(parent=None) -> GLViewWidget with the full stage scene
"""

from __future__ import annotations

import numpy as np

from pyqtgraph.opengl import (
    GLViewWidget,
    GLMeshItem,
    GLLinePlotItem,
    GLGridItem,
)
from pyqtgraph import MeshData

from shared.fixture_manager import get_fixture_manager


# ─── Geometry Helpers ────────────────────────────────────────────────

def _make_box_mesh(width: float, height: float, depth: float) -> MeshData:
    """Create a MeshData box with *width*, *height*, *depth* (centered at origin)."""
    w, h, d = width / 2, height / 2, depth / 2
    verts = np.array([
        [-w, -h, -d],  # 0  left-bottom-back
        [ w, -h, -d],  # 1  right-bottom-back
        [ w,  h, -d],  # 2  right-top-back
        [-w,  h, -d],  # 3  left-top-back
        [-w, -h,  d],  # 4  left-bottom-front
        [ w, -h,  d],  # 5  right-bottom-front
        [ w,  h,  d],  # 6  right-top-front
        [-w,  h,  d],  # 7  left-top-front
    ], dtype=float)

    faces = np.array([
        [0, 3, 2], [0, 2, 1],  # -Z back
        [4, 5, 6], [4, 6, 7],  # +Z front
        [0, 1, 5], [0, 5, 4],  # -Y bottom
        [2, 3, 7], [2, 7, 6],  # +Y top
        [0, 4, 7], [0, 7, 3],  # -X left
        [1, 2, 6], [1, 6, 5],  # +X right
    ], dtype=int)

    return MeshData(vertexes=verts, faces=faces)


def _make_cylinder_mesh(radius: float, height: float, segments: int = 16) -> MeshData:
    """Create a MeshData cylinder with *radius* and *height* (along Y, centered)."""
    h = height / 2
    angles = np.linspace(0, 2 * np.pi, segments + 1)
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)

    top = np.column_stack([radius * cos_a, np.full_like(cos_a, h), radius * sin_a])
    bot = np.column_stack([radius * cos_a, np.full_like(cos_a, -h), radius * sin_a])

    verts = np.vstack([
        top,
        bot,
        [[0, h, 0]],     # top center
        [[0, -h, 0]],    # bottom center
    ])

    top_c = 2 * segments + 1
    bot_c = 2 * segments + 2

    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.extend([
            [i, nxt, segments + 1 + i],
            [segments + 1 + i, nxt, segments + 1 + nxt],
        ])
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append([top_c, i, nxt])
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append([bot_c, segments + 1 + nxt, segments + 1 + i])

    return MeshData(vertexes=verts, faces=np.array(faces, dtype=int))


def _make_cone_mesh(radius: float, height: float, segments: int = 12) -> MeshData:
    """Create a MeshData cone (apex at +Y/2, base at -Y/2)."""
    h = height / 2
    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)

    base = np.column_stack([radius * cos_a, np.full_like(cos_a, -h), radius * sin_a])
    apex = np.array([[0, h, 0]])
    center = np.array([[0, -h, 0]])

    verts = np.vstack([base, apex, center])

    apex_idx = segments
    center_idx = segments + 1

    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append([apex_idx, i, nxt])
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append([center_idx, nxt, i])

    return MeshData(vertexes=verts, faces=np.array(faces, dtype=int))


# ─── Fixture Factories ───────────────────────────────────────────────

# Dark grey material for fixture housings
_FIXTURE_COLOR = (0.25, 0.25, 0.28, 1.0)

# Semi-transparent colors for beams
_BEAM_COLORS = {
    "white":  (1.0, 1.0, 1.0, 0.30),
    "red":    (1.0, 0.2, 0.2, 0.30),
    "blue":   (0.2, 0.4, 1.0, 0.30),
    "green":  (0.2, 0.8, 0.4, 0.30),
    "purple": (0.7, 0.3, 0.9, 0.30),
    "amber":  (1.0, 0.6, 0.2, 0.30),
}


def create_moving_head(pos=(0, 0, 0)):
    """
    Create a moving-head fixture geometry.

    Components:
      - Base:     20x20x10 box (dark grey)
      - Yoke:     inverted-U bracket made of 3 thin boxes (arms + crossbar)
      - Head:     cylinder ~14 diam x 30 long (the tube)
      - Lens:     small cone for the optic

    Returns a list of GLMeshItem instances (already offset to *pos*).
    """
    x, y, z = pos
    items = []

    # ── Base: 20 x 20 x 10 ──
    base = GLMeshItem(
        meshdata=_make_box_mesh(20, 10, 20),
        smooth=True,
        color=_FIXTURE_COLOR,
        shader="shaded",
        glOptions="opaque",
    )
    base.translate(x, y + 5, z)   # sit on the ground (Y is up)
    items.append(base)

    # ── Yoke: inverted-U (3 thin boxes) ──
    # Left vertical arm
    yoke_l = GLMeshItem(
        meshdata=_make_box_mesh(6, 24, 6),
        smooth=True, color=_FIXTURE_COLOR,
        shader="shaded", glOptions="opaque",
    )
    yoke_l.translate(x - 16, y + 17, z)
    items.append(yoke_l)

    # Right vertical arm
    yoke_r = GLMeshItem(
        meshdata=_make_box_mesh(6, 24, 6),
        smooth=True, color=_FIXTURE_COLOR,
        shader="shaded", glOptions="opaque",
    )
    yoke_r.translate(x + 16, y + 17, z)
    items.append(yoke_r)

    # Crossbar
    yoke_top = GLMeshItem(
        meshdata=_make_box_mesh(38, 6, 6),
        smooth=True, color=_FIXTURE_COLOR,
        shader="shaded", glOptions="opaque",
    )
    yoke_top.translate(x, y + 29, z)
    items.append(yoke_top)

    # ── Head (cylinder): Ø14 x 30 ──
    head = GLMeshItem(
        meshdata=_make_cylinder_mesh(7, 30),
        smooth=True, color=_FIXTURE_COLOR,
        shader="shaded", glOptions="opaque",
    )
    head.translate(x, y + 42, z)
    items.append(head)

    # ── Lens (cone): Ø10 x 16 ──
    lens = GLMeshItem(
        meshdata=_make_cone_mesh(5, 16),
        smooth=True, color=_FIXTURE_COLOR,
        shader="shaded", glOptions="opaque",
    )
    lens.translate(x, y + 58, z)
    items.append(lens)

    return items


def create_led_bar(pos=(0, 0, 0), rotation=0.0):
    """
    Create an LED bar fixture geometry.

    A long, thin box: 100 x 10 x 10 (dark grey).
    *rotation* is in degrees about the Y axis (0 = pointing +X).

    Returns a single GLMeshItem.
    """
    x, y, z = pos
    bar = GLMeshItem(
        meshdata=_make_box_mesh(100, 10, 10),
        smooth=True,
        color=_FIXTURE_COLOR,
        shader="shaded",
        glOptions="opaque",
    )
    bar.translate(x, y + 5, z)
    if rotation:
        bar.rotate(rotation, 0, 1, 0)
    return bar


def create_beam(start_pos=(0, 0, 0), end_pos=(0, 100, 0), color=(1.0, 1.0, 1.0, 0.3), beam_angle: float = 25.0):
    """
    Create a translucent light beam between two positions.

    Uses GLLinePlotItem with a thick line and RGBA colour with alpha=0.3.
    *beam_angle* (degrees) adjusts the line width to approximate the
    fixture's actual beam spread.

    Returns a GLLinePlotItem.
    """
    rgba = list(color)
    if len(rgba) == 3:
        rgba.append(0.3)

    # Line width scales with beam angle (clamped to reasonable range)
    width = max(2.0, min(beam_angle * 0.3, 20.0))

    start = np.array(start_pos, dtype=float)
    end = np.array(end_pos, dtype=float)

    pos = np.array([start, end])
    color_arr = np.array([rgba, rgba])

    beam = GLLinePlotItem(
        pos=pos,
        color=color_arr,
        width=width,
        antialias=True,
        mode="line_strip",
    )
    return beam


# ─── 3D View Widget ──────────────────────────────────────────────────

class Lightman3DView(GLViewWidget):
    """
    Full stage 3D view.

    Assembles:
      - GLGridItem floor (stage)
      - 2 Moving Heads (left and right of stage)
      - 2 LED Bars (stage front left / right)
      - Beams from Moving Heads toward stage centre

    Supports mouse drag (orbit), mouse wheel (zoom).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Camera settings
        self.setCameraPosition(distance=400, elevation=25, azimuth=-45)

        # ── Floor grid (stage) ──
        grid = GLGridItem()
        grid.scale(20, 20, 1)
        grid.setDepth(0)
        self.addItem(grid)

        # ── Moving Heads (stage front left / right, elevated) ──
        mh_left = create_moving_head(pos=(-120, 40, -100))
        for item in mh_left:
            self.addItem(item)

        mh_right = create_moving_head(pos=(120, 40, -100))
        for item in mh_right:
            self.addItem(item)

        # ── LED Bars (stage front-left / right) ──
        bar_left = create_led_bar(pos=(-80, 10, -110), rotation=30)
        self.addItem(bar_left)

        bar_right = create_led_bar(pos=(80, 10, -110), rotation=-30)
        self.addItem(bar_right)

        # ── Beams (from fixtures toward stage centre) ──
        # Beam angles looked up from the real fixture catalog for accuracy
        fm = get_fixture_manager()
        MH_FIXTURE_ID = "ROBE-DP2500"   # Moving head spot (beam ~2.0°)
        BAR_FIXTURE_ID = "CHAUVET-OVATION"  # LED bar wash (beam ~25.0°)
        mh_beam_angle = fm.get_beam_angle(MH_FIXTURE_ID)
        bar_beam_angle = fm.get_beam_angle(BAR_FIXTURE_ID)
        stage_centre = (0, 0, 0)

        # Moving head beams
        beam_lt = create_beam(
            start_pos=(-120, 40, -100),
            end_pos=stage_centre,
            color=_BEAM_COLORS["white"],
            beam_angle=mh_beam_angle,
        )
        self.addItem(beam_lt)

        beam_rt = create_beam(
            start_pos=(120, 40, -100),
            end_pos=stage_centre,
            color=_BEAM_COLORS["amber"],
            beam_angle=mh_beam_angle,
        )
        self.addItem(beam_rt)

        # LED bar beams
        beam_bl = create_beam(
            start_pos=(-80, 10, -110),
            end_pos=stage_centre,
            color=_BEAM_COLORS["blue"],
            beam_angle=bar_beam_angle,
        )
        self.addItem(beam_bl)

        beam_br = create_beam(
            start_pos=(80, 10, -110),
            end_pos=stage_centre,
            color=_BEAM_COLORS["green"],
            beam_angle=bar_beam_angle,
        )
        self.addItem(beam_br)

        # ── Faint axis helper (cross at origin) ──
        axis_lines = GLLinePlotItem(
            pos=np.array([
                [0, 0, 0], [30, 0, 0],    # X
                [0, 0, 0], [0, 30, 0],    # Y
                [0, 0, 0], [0, 0, 30],    # Z
            ]),
            color=np.array([
                [1, 0, 0, 0.6],  # X-red
                [1, 0, 0, 0.6],
                [0, 1, 0, 0.6],  # Y-green
                [0, 1, 0, 0.6],
                [0, 0, 1, 0.6],  # Z-blue
                [0, 0, 1, 0.6],
            ]),
            width=2.0,
            antialias=True,
        )
        self.addItem(axis_lines)
