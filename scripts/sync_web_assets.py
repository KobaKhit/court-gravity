#!/usr/bin/env python3
"""Copy synthetic JSON into web/public for static hosting / preview."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "data" / "synthetic"
dst = ROOT / "web" / "public" / "data"
dst.mkdir(parents=True, exist_ok=True)
if src.exists():
    for name in ("trajectories.json", "shader_uniforms.json", "court_config.json", "palette.json"):
        f = src / name
        if f.exists():
            shutil.copy2(f, dst / name)
    fields = src / "fields"
    if fields.exists():
        (dst / "fields").mkdir(exist_ok=True)
        for f in fields.glob("*_rgb.png"):
            shutil.copy2(f, dst / "fields" / f.name)
    print(f"Copied assets to {dst}")
else:
    print("No synthetic data yet — run scripts/generate_data.py first")
