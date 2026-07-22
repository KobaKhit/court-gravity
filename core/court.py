"""NBA half-court dimensions and coordinate helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

Origin = Literal["hoop", "center"]


@dataclass(frozen=True)
class CourtConfig:
    """NBA half-court geometry in feet."""

    length: float = 47.0  # baseline → half-court
    width: float = 50.0
    origin: Origin = "hoop"
    rim_x: float = 0.0
    rim_y: float = 0.0
    paint_width: float = 16.0
    paint_length: float = 19.0
    three_arc: float = 23.75
    three_corner: float = 22.0
    default_sigma: float = 5.0
    nx: int = 201
    ny: int = 189
    scene_scale: float = 0.1

    @property
    def x_extent(self) -> tuple[float, float]:
        """Court x range (sideline to sideline), origin-aware."""
        half_w = self.width / 2.0
        if self.origin == "hoop":
            return (-half_w, half_w)
        # center origin: hoop at y=-length/2 along length axis; x still centered
        return (-half_w, half_w)

    @property
    def y_extent(self) -> tuple[float, float]:
        """Court y range (baseline → half-court), origin-aware."""
        if self.origin == "hoop":
            # hoop near baseline; y increases toward half-court
            return (0.0, self.length)
        half_l = self.length / 2.0
        return (-half_l, half_l)

    def meshgrid(self, nx: int | None = None, ny: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        nx = nx or self.nx
        ny = ny or self.ny
        x0, x1 = self.x_extent
        y0, y1 = self.y_extent
        xs = np.linspace(x0, x1, nx)
        ys = np.linspace(y0, y1, ny)
        return np.meshgrid(xs, ys, indexing="xy")

    def to_scene(self, x: float, y: float, z: float = 0.0) -> tuple[float, float, float]:
        """Scale court feet to Manim/Three scene units."""
        s = self.scene_scale
        return (x * s, y * s, z * s)


def load_court_config(path: str | Path | None = None) -> CourtConfig:
    """Load court config from JSON, falling back to defaults."""
    if path is None:
        root = Path(__file__).resolve().parents[1]
        path = root / "configs" / "court_config.json"
    path = Path(path)
    if not path.exists():
        return CourtConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    hc = data.get("half_court", {})
    rim = data.get("rim", {})
    paint = data.get("paint", {})
    three = data.get("three_point", {})
    grid = data.get("grid", {})
    return CourtConfig(
        length=float(hc.get("length", 47.0)),
        width=float(hc.get("width", 50.0)),
        origin=data.get("origin", "hoop"),
        rim_x=float(rim.get("x", 0.0)),
        rim_y=float(rim.get("y", 0.0)),
        paint_width=float(paint.get("width", 16.0)),
        paint_length=float(paint.get("length", 19.0)),
        three_arc=float(three.get("arc_radius", 23.75)),
        three_corner=float(three.get("corner_distance", 22.0)),
        default_sigma=float(data.get("default_sigma_ft", 5.0)),
        nx=int(grid.get("nx", 201)),
        ny=int(grid.get("ny", 189)),
        scene_scale=float(data.get("scene_scale", 0.1)),
    )


def sample_three_point_ring(
    court: CourtConfig,
    n: int = 24,
    corner_pad: float = 3.0,
) -> np.ndarray:
    """Sample points along the 3-point arc (excluding deep corners padding)."""
    half_w = court.width / 2.0
    # Corner 3PT lines are vertical at ±22 ft from center for NBA; arc radius 23.75
    # Sample arc from angle covering the top of the key region
    x_corner = half_w - corner_pad
    # Clamp to arc
    max_x = min(x_corner, court.three_arc - 0.5)
    xs = np.linspace(-max_x, max_x, n)
    ys = np.sqrt(np.maximum(court.three_arc**2 - xs**2, 0.0))
    # Shift so arc is relative to rim at (0,0) with hoop origin
    return np.column_stack([xs, ys])
