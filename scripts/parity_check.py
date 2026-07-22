#!/usr/bin/env python3
"""Compare Python field grid to a reference GLSL-equivalent CPU evaluation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.court import load_court_config
from core.export import players_to_shader_uniforms
from core.field import Player, evaluate_grid


def glsl_equivalent(XX: np.ndarray, YY: np.ndarray, uniforms: dict) -> np.ndarray:
    """Mirror the web vertex-shader Gaussian loop in NumPy."""
    Z = np.zeros_like(XX)
    count = uniforms["uCount"]
    for i in range(count):
        px, py, signed_mass = uniforms["uPlayers"][i]
        s = uniforms["uSigma"][i]
        d2 = (XX - px) ** 2 + (YY - py) ** 2
        Z += signed_mass * np.exp(-d2 / (2.0 * s * s))
    return Z


def main() -> None:
    court = load_court_config()
    players = [
        Player(x=0.0, y=20.0, mass=1.2, sigma=5.0, team="offense", id="a"),
        Player(x=-12.0, y=14.0, mass=0.9, sigma=4.5, team="offense", id="b"),
        Player(x=8.0, y=18.0, mass=1.0, sigma=5.0, team="defense", id="c"),
    ]
    XX, YY, Z_py = evaluate_grid(players, court, nx=101, ny=95)
    uniforms = players_to_shader_uniforms(players)
    Z_gl = glsl_equivalent(XX, YY, uniforms)
    err = np.max(np.abs(Z_py - Z_gl))
    print(f"max abs error Python vs GLSL-equiv: {err:.6e}")
    out = ROOT / "data" / "parity"
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "Z_python.npy", Z_py)
    np.save(out / "Z_glsl_equiv.npy", Z_gl)
    (out / "report.json").write_text(
        json.dumps({"max_abs_error": float(err), "pass": bool(err < 1e-5)}, indent=2),
        encoding="utf-8",
    )
    if err >= 1e-5:
        raise SystemExit(f"PARITY FAIL: {err}")
    print("PARITY OK")


if __name__ == "__main__":
    main()
