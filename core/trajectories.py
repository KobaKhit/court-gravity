"""Synthetic player trajectories: spring-damper + Perlin wander + set plays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .noiseutil import pnoise2
from .court import CourtConfig, load_court_config


@dataclass
class TrajectoryConfig:
    dt: float = 1.0 / 30.0
    duration: float = 12.0
    spring_k: float = 4.0
    damping_c: float = 2.5
    noise_amp: float = 3.0
    noise_scale: float = 0.15
    seed: int = 0


@dataclass
class AgentState:
    id: str
    role: str
    team: str
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    anchor_x: float = 0.0
    anchor_y: float = 0.0
    mass: float = 1.0
    sigma: float = 5.0
    respect: float = 0.7  # defense: α toward assigned offender
    assigned_offense_id: str | None = None
    noise_ox: float = 0.0
    noise_oy: float = 0.0


def _perlin_offset(t: float, ox: float, oy: float, amp: float, scale: float) -> tuple[float, float]:
    nx = pnoise2(t * scale + ox, oy, repeatx=1024, repeaty=1024, base=0)
    ny = pnoise2(ox, t * scale + oy, repeatx=1024, repeaty=1024, base=1)
    return amp * nx, amp * ny


def step_agents(
    agents: list[AgentState],
    ball: tuple[float, float],
    t: float,
    cfg: TrajectoryConfig,
    court: CourtConfig,
) -> None:
    """Advance all agents one physics step in-place."""
    by_id = {a.id: a for a in agents}
    x0, x1 = court.x_extent
    y0, y1 = court.y_extent

    for a in agents:
        if a.team == "defense" and a.assigned_offense_id and a.assigned_offense_id in by_id:
            off = by_id[a.assigned_offense_id]
            alpha = a.respect
            target_x = alpha * off.x + (1.0 - alpha) * ball[0]
            target_y = alpha * off.y + (1.0 - alpha) * ball[1]
        else:
            nox, noy = _perlin_offset(t, a.noise_ox, a.noise_oy, cfg.noise_amp, cfg.noise_scale)
            target_x = a.anchor_x + nox
            target_y = a.anchor_y + noy

        ax = -cfg.spring_k * (a.x - target_x) - cfg.damping_c * a.vx
        ay = -cfg.spring_k * (a.y - target_y) - cfg.damping_c * a.vy
        a.vx += ax * cfg.dt
        a.vy += ay * cfg.dt
        a.x = float(np.clip(a.x + a.vx * cfg.dt, x0, x1))
        a.y = float(np.clip(a.y + a.vy * cfg.dt, y0, y1))


def simulate(
    agents: list[AgentState],
    *,
    court: CourtConfig | None = None,
    cfg: TrajectoryConfig | None = None,
    ball_fn: Callable[[float], tuple[float, float]] | None = None,
) -> dict:
    """
    Simulate trajectories.

    Returns schema:
      {players:[{id,role,team,stats,traj:[[t,x,y],…]}], ball:[[t,x,y],…], dt, duration}
    """
    court = court or load_court_config()
    cfg = cfg or TrajectoryConfig()
    rng = np.random.default_rng(cfg.seed)

    for i, a in enumerate(agents):
        a.noise_ox = float(rng.uniform(0, 100))
        a.noise_oy = float(rng.uniform(0, 100))
        a.x, a.y = a.anchor_x, a.anchor_y

    n_steps = int(cfg.duration / cfg.dt)
    trajs: dict[str, list[list[float]]] = {a.id: [] for a in agents}
    ball_traj: list[list[float]] = []

    def default_ball(t: float) -> tuple[float, float]:
        # Gentle orbit near top of key
        return (8.0 * np.sin(0.4 * t), 18.0 + 4.0 * np.cos(0.35 * t))

    ball_fn = ball_fn or default_ball

    for step in range(n_steps + 1):
        t = step * cfg.dt
        bx, by = ball_fn(t)
        ball_traj.append([t, float(bx), float(by)])
        for a in agents:
            trajs[a.id].append([t, a.x, a.y])
        if step < n_steps:
            step_agents(agents, (bx, by), t, cfg, court)

    players_out = []
    for a in agents:
        players_out.append(
            {
                "id": a.id,
                "role": a.role,
                "team": a.team,
                "stats": {
                    "base_mass": a.mass,
                    "sigma": a.sigma,
                    "respect": a.respect,
                },
                "traj": trajs[a.id],
            }
        )
    return {
        "players": players_out,
        "ball": ball_traj,
        "dt": cfg.dt,
        "duration": cfg.duration,
    }


# --- Scripted set plays (keyframe splines) ---------------------------------

def lerp_polyline(keyframes: list[tuple[float, float, float]], t: float) -> tuple[float, float]:
    """keyframes: list of (t, x, y)."""
    if t <= keyframes[0][0]:
        return keyframes[0][1], keyframes[0][2]
    if t >= keyframes[-1][0]:
        return keyframes[-1][1], keyframes[-1][2]
    for i in range(len(keyframes) - 1):
        t0, x0, y0 = keyframes[i]
        t1, x1, y1 = keyframes[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-9)
            return x0 + u * (x1 - x0), y0 + u * (y1 - y0)
    return keyframes[-1][1], keyframes[-1][2]


def pick_and_roll_keyframes() -> dict[str, list[tuple[float, float, float]]]:
    """Simple PnR: ball-handler + screener + roll."""
    return {
        "pg": [(0, 0, 28), (2, -4, 22), (4, -2, 18), (6, 2, 16), (8, 5, 14)],
        "c": [(0, 4, 16), (2, -2, 20), (4, -4, 18), (6, 0, 8), (8, 2, 4)],
        "ball": [(0, 0, 28), (2, -4, 22), (4, -3, 17), (6, 0, 10), (8, 2, 5)],
    }
