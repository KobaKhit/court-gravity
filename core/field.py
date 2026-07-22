"""Influence kernels, signed court surface, and gradients."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

import numpy as np

from .court import CourtConfig, load_court_config


class FieldMode(str, Enum):
    NET = "net"
    OFFENSE = "offense"
    DEFENSE = "defense"


class KernelType(str, Enum):
    GAUSSIAN = "gaussian"
    SOFTENED = "softened"  # Newtonian Φ = -G m / sqrt(r² + ε²)


@dataclass
class Player:
    """A player contributing to the influence field."""

    x: float
    y: float
    mass: float = 1.0
    sigma: float = 5.0
    team: str = "offense"  # "offense" | "defense"
    vx: float = 0.0
    vy: float = 0.0
    id: str = ""
    role: str = ""
    # Optional spatially-varying effectiveness multiplier sampled on evaluation
    effectiveness: np.ndarray | None = None  # shape (ny, nx) aligned with grid
    # Softened-potential extras
    softening: float = 2.0
    G: float = 1.0
    # Anisotropic stretch (Fernández–Bornn style); 0 = isotropic
    anisotropy: float = 0.0

    @property
    def signed_mass(self) -> float:
        """Offense digs wells (negative contribution to z via -Σ); defense raises ridges."""
        return self.mass


def _anisotropic_quad(
    dx: np.ndarray,
    dy: np.ndarray,
    sigma: float,
    vx: float,
    vy: float,
    anisotropy: float,
) -> np.ndarray:
    """Quadratic form rᵀ Σ⁻¹ r for (optionally) anisotropic Gaussian."""
    if anisotropy <= 1e-6 or (abs(vx) + abs(vy)) < 1e-9:
        return (dx * dx + dy * dy) / (sigma * sigma)

    speed = np.hypot(vx, vy)
    # ρ stretches along velocity; clamp
    rho = float(np.clip(anisotropy * min(speed / 10.0, 1.0) ** 2, 0.0, 0.85))
    theta = np.arctan2(vy, vx)
    c, s = np.cos(theta), np.sin(theta)
    # rotate into velocity frame
    rx = c * dx + s * dy
    ry = -s * dx + c * dy
    sx = sigma * (1.0 + rho)
    sy = sigma * (1.0 - rho)
    return (rx * rx) / (sx * sx) + (ry * ry) / (sy * sy)


def influence(
    x: np.ndarray | float,
    y: np.ndarray | float,
    player: Player,
    kernel: KernelType = KernelType.GAUSSIAN,
) -> np.ndarray:
    """Scalar influence I_i(x,y) ≥ 0 (before team sign)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    dx = x - player.x
    dy = y - player.y

    if kernel == KernelType.SOFTENED:
        r2 = dx * dx + dy * dy
        eps2 = player.softening ** 2
        # Use positive magnitude; sign applied in superposition
        val = player.G * player.mass / np.sqrt(r2 + eps2)
    else:
        quad = _anisotropic_quad(dx, dy, player.sigma, player.vx, player.vy, player.anisotropy)
        val = player.mass * np.exp(-0.5 * quad)

    return val


def influence_gradient(
    x: np.ndarray | float,
    y: np.ndarray | float,
    player: Player,
    kernel: KernelType = KernelType.GAUSSIAN,
) -> tuple[np.ndarray, np.ndarray]:
    """∂I/∂x, ∂I/∂y for analytic gradient of a single kernel."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    dx = x - player.x
    dy = y - player.y
    I = influence(x, y, player, kernel)

    if kernel == KernelType.SOFTENED:
        r2 = dx * dx + dy * dy
        eps2 = player.softening ** 2
        denom = (r2 + eps2) ** 1.5
        # I = G m / sqrt(r²+ε²) → ∇I = -G m (x-x0) / (r²+ε²)^{3/2}
        gx = -player.G * player.mass * dx / denom
        gy = -player.G * player.mass * dy / denom
        return gx, gy

    # Isotropic / mild anisotropic approx: ∇I = -I · Σ⁻¹ r
    s2 = player.sigma ** 2
    gx = -I * dx / s2
    gy = -I * dy / s2
    return gx, gy


def _team_sign(player: Player) -> float:
    """Contribution multiplier for z: offense → negative well, defense → positive ridge."""
    return -1.0 if player.team == "offense" else 1.0


def _sample_effectiveness(
    player: Player,
    x: np.ndarray,
    y: np.ndarray,
    court: CourtConfig,
) -> np.ndarray | float:
    if player.effectiveness is None:
        return 1.0
    # Map world coords to grid indices
    x0, x1 = court.x_extent
    y0, y1 = court.y_extent
    ny, nx = player.effectiveness.shape
    xi = (x - x0) / max(x1 - x0, 1e-9) * (nx - 1)
    yi = (y - y0) / max(y1 - y0, 1e-9) * (ny - 1)
    xi = np.clip(np.round(xi).astype(int), 0, nx - 1)
    yi = np.clip(np.round(yi).astype(int), 0, ny - 1)
    return player.effectiveness[yi, xi]


def court_surface(
    x: np.ndarray | float,
    y: np.ndarray | float,
    players: Sequence[Player],
    *,
    t: float = 0.0,
    mode: FieldMode | str = FieldMode.NET,
    kernel: KernelType | str = KernelType.GAUSSIAN,
    court: CourtConfig | None = None,
) -> np.ndarray:
    """
    Signed court height z(x,y).

    z = -Σ_offense I_i + Σ_defense I_j   (for mode=net)
    """
    _ = t  # reserved for time-varying fields / trajectories applied externally
    court = court or load_court_config()
    mode = FieldMode(mode)
    kernel = KernelType(kernel)

    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.zeros_like(x, dtype=np.float64)

    for p in players:
        if mode == FieldMode.OFFENSE and p.team != "offense":
            continue
        if mode == FieldMode.DEFENSE and p.team != "defense":
            continue
        I = influence(x, y, p, kernel)
        g = _sample_effectiveness(p, x, y, court)
        contrib = _team_sign(p) * I * g
        if mode == FieldMode.OFFENSE:
            # Show wells as negative even when viewing offense alone
            contrib = -np.abs(I * g) if p.team == "offense" else contrib
        elif mode == FieldMode.DEFENSE:
            contrib = np.abs(I * g) if p.team == "defense" else contrib
        z = z + contrib
    return z


def evaluate_grid(
    players: Sequence[Player],
    court: CourtConfig | None = None,
    *,
    mode: FieldMode | str = FieldMode.NET,
    kernel: KernelType | str = KernelType.GAUSSIAN,
    nx: int | None = None,
    ny: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return XX, YY, Z on a regular court grid."""
    court = court or load_court_config()
    XX, YY = court.meshgrid(nx, ny)
    Z = court_surface(XX, YY, players, mode=mode, kernel=kernel, court=court)
    return XX, YY, Z


def gradient_grid(
    players: Sequence[Player],
    court: CourtConfig | None = None,
    *,
    mode: FieldMode | str = FieldMode.NET,
    kernel: KernelType | str = KernelType.GAUSSIAN,
    nx: int | None = None,
    ny: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return XX, YY, dZ/dx, dZ/dy via analytic per-player gradients."""
    court = court or load_court_config()
    mode = FieldMode(mode)
    kernel = KernelType(kernel)
    XX, YY = court.meshgrid(nx, ny)
    gx = np.zeros_like(XX)
    gy = np.zeros_like(YY)

    for p in players:
        if mode == FieldMode.OFFENSE and p.team != "offense":
            continue
        if mode == FieldMode.DEFENSE and p.team != "defense":
            continue
        igx, igy = influence_gradient(XX, YY, p, kernel)
        g = _sample_effectiveness(p, XX, YY, court)
        s = _team_sign(p)
        if mode == FieldMode.OFFENSE:
            s = -1.0
        elif mode == FieldMode.DEFENSE:
            s = 1.0
        gx = gx + s * igx * g
        gy = gy + s * igy * g
    return XX, YY, gx, gy


def integrate_marble(
    players: Sequence[Player],
    start: tuple[float, float],
    *,
    court: CourtConfig | None = None,
    dt: float = 0.02,
    steps: int = 400,
    damping: float = 1.5,
    mode: FieldMode | str = FieldMode.NET,
    kernel: KernelType | str = KernelType.GAUSSIAN,
) -> np.ndarray:
    """
    Integrate p'' = -∇z - damping·p' (marble rolls into wells).
    Returns array of shape (steps+1, 2).
    """
    court = court or load_court_config()
    x0, x1 = court.x_extent
    y0, y1 = court.y_extent
    pos = np.array(start, dtype=np.float64)
    vel = np.zeros(2, dtype=np.float64)
    path = [pos.copy()]

    for _ in range(steps):
        # Recompute at exact point
        gxv = 0.0
        gyv = 0.0
        mode_e = FieldMode(mode)
        kern = KernelType(kernel)
        for p in players:
            if mode_e == FieldMode.OFFENSE and p.team != "offense":
                continue
            if mode_e == FieldMode.DEFENSE and p.team != "defense":
                continue
            igx, igy = influence_gradient(pos[0], pos[1], p, kern)
            g = _sample_effectiveness(p, np.array(pos[0]), np.array(pos[1]), court)
            s = _team_sign(p)
            if mode_e == FieldMode.OFFENSE:
                s = -1.0
            elif mode_e == FieldMode.DEFENSE:
                s = 1.0
            gxv += float(s * igx * g)
            gyv += float(s * igy * g)

        acc = np.array([-gxv, -gyv]) - damping * vel
        vel = vel + acc * dt
        pos = pos + vel * dt
        pos[0] = float(np.clip(pos[0], x0, x1))
        pos[1] = float(np.clip(pos[1], y0, y1))
        path.append(pos.copy())

    return np.asarray(path)
