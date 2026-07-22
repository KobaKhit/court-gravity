#!/usr/bin/env python3
"""Ship checklist: regenerate data, sync web assets, rebuild frontend, verify tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd or ROOT)


def main() -> None:
    run([str(PY), "scripts/sanity_plot.py"])
    run([str(PY), "scripts/parity_check.py"])
    run([str(PY), "scripts/generate_data.py"])
    run([str(PY), "scripts/sync_web_assets.py"])
    run([str(PY), "manim_video/render_matplotlib.py"])
    run([str(PY), "-m", "pytest", "-q"])
    run(["npm", "run", "build"], cwd=ROOT / "web")
    print("\nShip artifacts:")
    print(f"  Web build:       {ROOT / 'web' / 'dist'}")
    print(f"  Storyboard:      {ROOT / 'data' / 'storyboard'}")
    print(f"  Synthetic data:  {ROOT / 'data' / 'synthetic'}")
    print(f"  Parity report:   {ROOT / 'data' / 'parity' / 'report.json'}")
    print(f"  Blender script:  {ROOT / 'blender' / 'bake_heightmaps.py'}")
    print("\nPreview web: cd web && npm run preview")


if __name__ == "__main__":
    main()
