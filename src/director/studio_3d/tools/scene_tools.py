"""Scene tools — helpers for building pyqtgraph.opengl items.

`pyqtgraph.opengl` does not ship GLBoxItem / GLCylinderItem. This module
builds the equivalents explicitly:

    create_truss(...)   -> GLLinePlotItem   (wireframe box, mode='lines')
    create_stand(...)   -> GLMeshItem       (solid cylinder)
    load_obj(...)       -> GLMeshItem       (from OBJ file)
"""

import os

import numpy as np
from pyqtgraph.opengl import GLMeshItem, GLLinePlotItem, MeshData


def _box_edge_vertices(length: float, height: float, width: float):
    "Return vertex array of 8 box corners and a list of 12 edges."
    hx = width / 2.0
    hz = length / 2.0
    hy = height

    verts = np.array(
        [
            [-hx, 0.0, -hz],
            [hx, 0.0, -hz],
            [hx, 0.0, hz],
            [-hx, 0.0, hz],
            [-hx, hy, -hz],
            [hx, hy, -hz],
            [hx, hy, hz],
            [-hx, hy, hz],
        ],
        dtype=float,
    )
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    return verts, edges


def _cylinder_mesh(radius: float, height: float, segments: int = 24):
    "Return (vertexes Nx3, faces Mx3) for a solid cylinder."
    vertexes = [[0.0, 0.0, 0.0]]

    for i in range(segments):
        angle = 2.0 * np.pi * i / segments
        vertexes.append(
            [radius * np.cos(angle), 0.0, radius * np.sin(angle)]
        )

    top_center = len(vertexes)
    vertexes.append([0.0, height, 0.0])

    for i in range(segments):
        angle = 2.0 * np.pi * i / segments
        vertexes.append(
            [radius * np.cos(angle), height, radius * np.sin(angle)]
        )

    faces = []
    for i in range(segments):
        bottom_a = 1 + i
        bottom_b = 1 + ((i + 1) % segments)
        top_a = top_center + 1 + i
        top_b = top_center + 1 + ((i + 1) % segments)

        faces.append([bottom_a, bottom_b, top_b])
        faces.append([bottom_a, top_b, top_a])
        faces.append([0, bottom_b, bottom_a])
        faces.append([top_center, top_a, top_b])

    return np.array(vertexes, dtype=float), np.array(faces, dtype=int)


def _parse_obj(filepath: str):
    "Minimal OBJ parser: 'v' and 'f' lines only."
    vertexes = []
    faces = []

    with open(filepath, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            tag = parts[0]
            if tag == "v":
                vertexes.append(
                    [float(parts[1]), float(parts[2]), float(parts[3])]
                )
            elif tag == "f":
                face = []
                for token in parts[1:4]:
                    idx_str = token.split("/")[0]
                    idx = int(idx_str)
                    if idx < 0:
                        idx = len(vertexes) + idx
                    else:
                        idx = idx - 1
                    face.append(idx)
                if len(face) == 3:
                    faces.append(face)

    return (
        np.array(vertexes, dtype=float),
        np.array(faces, dtype=int),
    )


class SceneTools:
    "Stateless factory for scene geometry items."

    @staticmethod
    def load_obj(filepath: str) -> GLMeshItem:
        "Load an OBJ file and return a GLMeshItem."
        if not os.path.isfile(filepath):
            raise FileNotFoundError(filepath)

        vertexes, faces = _parse_obj(filepath)
        if len(vertexes) == 0 or len(faces) == 0:
            raise ValueError(f"OBJ has no geometry: {filepath}")

        mesh = MeshData(vertexes=vertexes, faces=faces)
        item = GLMeshItem(
            meshdata=mesh,
            smooth=False,
            drawFaces=True,
            drawEdges=True,
            edgeColor=(0.4, 0.4, 0.4, 1.0),
            faceColor=(0.7, 0.7, 0.7, 1.0),
        )
        return item

    @staticmethod
    def create_truss(
        length: float = 2.0,
        height: float = 0.3,
        width: float = 0.3,
    ) -> GLLinePlotItem:
        "Return a wireframe box (truss) as a line plot."
        verts, edges = _box_edge_vertices(length, height, width)

        pos = []
        for a, b in edges:
            pos.append(verts[a])
            pos.append(verts[b])

        item = GLLinePlotItem(
            pos=np.array(pos, dtype=float),
            color=(0.85, 0.85, 0.85, 1.0),
            width=2.0,
            antialias=True,
            mode="lines",
        )
        return item

    @staticmethod
    def create_stand(height: float = 1.0, radius: float = 0.06) -> GLMeshItem:
        "Return a solid cylinder (stand) as a mesh item."
        vertexes, faces = _cylinder_mesh(radius=radius, height=height)
        mesh = MeshData(vertexes=vertexes, faces=faces)
        item = GLMeshItem(
            meshdata=mesh,
            smooth=True,
            drawFaces=True,
            drawEdges=False,
            color=(0.5, 0.5, 0.55, 1.0),
        )
        return item