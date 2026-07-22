"""Export grids, heightmaps, and trajectory JSON for Manim / web / Blender."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image

from .court import CourtConfig, load_court_config
from .field import FieldMode, KernelType, Player, evaluate_grid


def export_npy(path: str | Path, Z: np.ndarray) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, Z.astype(np.float32))
    return path


def export_float32_bin(path: str | Path, Z: np.ndarray) -> Path:
    """Raw Float32 row-major for Three.js DataTexture."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Z.astype(np.float32).tofile(path)
    return path


def export_heightmap_png(
    path: str | Path,
    Z: np.ndarray,
    *,
    vmax: float | None = None,
) -> Path:
    """
    16-bit grayscale PNG. Mid-gray = 0; darker = wells; brighter = peaks.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    vmax = vmax or float(max(abs(Z.min()), abs(Z.max()), 1e-6))
    norm = np.clip((Z / vmax) * 0.5 + 0.5, 0.0, 1.0)
    img16 = (norm * 65535).astype(np.uint16)
    Image.fromarray(img16, mode="I;16").save(path)
    return path


def export_heightmap_rgb(
    path: str | Path,
    Z: np.ndarray,
    *,
    vmax: float | None = None,
) -> Path:
    """8-bit RGB preview: blue wells → black flat → yellow peaks."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    vmax = vmax or float(max(abs(Z.min()), abs(Z.max()), 1e-6))
    t = np.clip(Z / vmax, -1.0, 1.0)
    rgb = np.zeros(Z.shape + (3,), dtype=np.uint8)
    well = np.array([0.05, 0.15, 0.45])
    flat = np.array([0.02, 0.02, 0.06])
    peak = np.array([1.0, 0.85, 0.2])
    neg = t < 0
    pos = ~neg
    for c in range(3):
        channel = np.where(
            neg,
            flat[c] + (well[c] - flat[c]) * (-t),
            flat[c] + (peak[c] - flat[c]) * t,
        )
        rgb[..., c] = (np.clip(channel, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(rgb, mode="RGB").save(path)
    return path


def export_field(
    out_dir: str | Path,
    players: Sequence[Player],
    *,
    court: CourtConfig | None = None,
    mode: FieldMode | str = FieldMode.NET,
    kernel: KernelType | str = KernelType.GAUSSIAN,
    stem: str = "field",
) -> dict:
    """Write npy, float bin, 16-bit PNG, RGB preview, and metadata JSON."""
    court = court or load_court_config()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    XX, YY, Z = evaluate_grid(players, court, mode=mode, kernel=kernel)
    export_npy(out_dir / f"{stem}.npy", Z)
    export_float32_bin(out_dir / f"{stem}.bin", Z)
    export_heightmap_png(out_dir / f"{stem}_h16.png", Z)
    export_heightmap_rgb(out_dir / f"{stem}_rgb.png", Z)
    meta = {
        "stem": stem,
        "shape": list(Z.shape),
        "ny": int(Z.shape[0]),
        "nx": int(Z.shape[1]),
        "x_extent": list(court.x_extent),
        "y_extent": list(court.y_extent),
        "mode": str(mode),
        "kernel": str(kernel),
        "z_min": float(Z.min()),
        "z_max": float(Z.max()),
        "players": [
            {
                "id": p.id,
                "x": p.x,
                "y": p.y,
                "mass": p.mass,
                "sigma": p.sigma,
                "team": p.team,
                "role": p.role,
            }
            for p in players
        ],
    }
    (out_dir / f"{stem}_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def export_trajectories_json(path: str | Path, data: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def players_to_shader_uniforms(players: Sequence[Player], max_players: int = 16) -> dict:
    """Pack players for GLSL uPlayers[16] / uSigma[16] / uCount."""
    arr = []
    sigmas = []
    for p in list(players)[:max_players]:
        signed = -p.mass if p.team == "offense" else p.mass
        arr.append([p.x, p.y, signed])
        sigmas.append(p.sigma)
    while len(arr) < max_players:
        arr.append([0.0, 0.0, 0.0])
        sigmas.append(5.0)
    return {
        "uPlayers": arr,
        "uSigma": sigmas,
        "uCount": min(len(players), max_players),
    }
