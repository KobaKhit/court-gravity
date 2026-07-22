"""
Optional Blender bake script.

Run inside Blender:
  blender --background --python blender/bake_heightmaps.py

Requires a prior `python scripts/generate_data.py` so data/synthetic/fields/*.npy exist.
Creates a subdivided plane and assigns an image-sequence displacement from exported PNGs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bake_with_bpy() -> None:
    import bpy
    import numpy as np

    field_dir = ROOT / "data" / "synthetic" / "fields"
    rgb = field_dir / "full_lineup_rgb.png"
    if not rgb.exists():
        print(f"Missing {rgb}; run scripts/generate_data.py first")
        return

    # Clear default cube
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    plane = bpy.context.active_object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=100)
    bpy.ops.object.mode_set(mode="OBJECT")

    mat = bpy.data.materials.new(name="CourtGravity")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(rgb))
    tex.image.colorspace_settings.name = "Non-Color"
    disp = nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = 0.8
    links.new(tex.outputs["Color"], disp.inputs["Height"])
    links.new(disp.outputs["Displacement"], out.inputs["Displacement"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    plane.data.materials.append(mat)

    # Enable true displacement in Cycles
    bpy.context.scene.render.engine = "CYCLES"
    for mod in plane.modifiers:
        pass
    plane.modifiers.new("Subdivision", "SUBSURF")
    print("Blender court plane ready with displacement from", rgb)


if __name__ == "__main__":
    try:
        bake_with_bpy()
    except ImportError:
        print("bpy not available — open this script inside Blender.")
        sys.exit(0)
