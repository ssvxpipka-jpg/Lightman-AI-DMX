#!/usr/bin/env python3
"""Export Lightman scene.json to MVR format using pymvr."""
import json
import sys
from pathlib import Path

import pymvr


def export_scene_to_mvr(scene_data: dict, output_path: str):
    """
    Convert scene.json data into an MVR file using pymvr.

    Maps fixture fields:
    - id -> FixtureID
    - name -> Name
    - dmx_address -> DmxAddress
    - position -> Position (x, y, z)
    - rotation -> Rotation (rx, ry, rz)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mvr_writer = pymvr.GeneralSceneDescriptionWriter()

    # Build the MVR object tree
    scene_obj = pymvr.Scene()
    layers = pymvr.Layers()
    scene_obj.layers = layers

    # Create a layer
    layer = pymvr.Layer(name="Lightman Scene")
    layers.append(layer)

    # Create child list for the layer
    child_list = pymvr.ChildList()
    layer.child_list = child_list

    # Map fixtures from scene data
    fixtures_data = scene_data.get("fixtures", [])
    for fx in fixtures_data:
        fixture = pymvr.Fixture(
            name=fx.get("name", "Unnamed"),
            # Map DMX address if available
            dmx_address=fx.get("dmx_address"),
            # Map position
            position=fx.get("position", [0.0, 0.0, 0.0]),
            # Map rotation
            rotation=fx.get("rotation", [0.0, 0.0, 0.0]),
        )
        child_list.append(fixture)

    # Serialize and write
    mvr_writer.serialize_scene(scene_obj)
    mvr_writer.write_mvr(str(output_path))

    print(f"MVR file written to: {output_path}")