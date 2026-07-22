"""Unit tests for the field core."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.archetypes import make_player
from core.court import load_court_config
from core.field import (
    FieldMode,
    KernelType,
    Player,
    court_surface,
    evaluate_grid,
    influence,
    integrate_marble,
)
from core.trajectories import AgentState, TrajectoryConfig, simulate


def test_offense_digs_well():
    p = Player(0, 20, mass=1.0, sigma=5.0, team="offense")
    z = court_surface(0.0, 20.0, [p])
    assert z < 0


def test_defense_raises_ridge():
    p = Player(0, 20, mass=1.0, sigma=5.0, team="defense")
    z = court_surface(0.0, 20.0, [p])
    assert z > 0


def test_gaussian_peak_equals_mass():
    p = Player(0, 20, mass=1.7, sigma=5.0, team="offense")
    I = influence(0.0, 20.0, p)
    assert abs(float(I) - 1.7) < 1e-9


def test_softened_finite_at_center():
    p = Player(0, 20, mass=1.0, softening=2.0, G=1.0, team="offense")
    I = influence(0.0, 20.0, p, kernel=KernelType.SOFTENED)
    assert np.isfinite(I) and I > 0


def test_modes():
    off = Player(0, 20, mass=1.0, team="offense")
    de = Player(5, 20, mass=1.0, team="defense")
    z_net = court_surface(0.0, 20.0, [off, de], mode=FieldMode.NET)
    z_off = court_surface(0.0, 20.0, [off, de], mode=FieldMode.OFFENSE)
    z_def = court_surface(5.0, 20.0, [off, de], mode=FieldMode.DEFENSE)
    assert z_off < 0 and z_def > 0
    assert z_net != z_off


def test_grid_shape():
    court = load_court_config()
    _, _, Z = evaluate_grid([Player(0, 15, team="offense")], court, nx=50, ny=40)
    assert Z.shape == (40, 50)


def test_archetype_effectiveness():
    p = make_player("sharpshooter", with_effectiveness=True)
    assert p.effectiveness is not None
    assert p.effectiveness.max() <= 1.0 + 1e-6


def test_simulate_trajectories():
    agents = [
        AgentState("pg", "playmaker", "offense", 0, 26, anchor_x=0, anchor_y=26),
        AgentState(
            "d0",
            "lockdown",
            "defense",
            0,
            22,
            anchor_x=0,
            anchor_y=22,
            assigned_offense_id="pg",
            respect=0.8,
        ),
    ]
    data = simulate(agents, cfg=TrajectoryConfig(duration=1.0, dt=0.1, seed=1))
    assert len(data["players"]) == 2
    assert len(data["players"][0]["traj"]) == 11


def test_marble_moves_toward_well():
    p = Player(0, 20, mass=2.0, sigma=6.0, team="offense")
    path = integrate_marble([p], start=(8.0, 20.0), steps=200, dt=0.03, damping=2.0)
    # Should get closer to the well center
    d0 = np.hypot(path[0, 0] - 0, path[0, 1] - 20)
    d1 = np.hypot(path[-1, 0] - 0, path[-1, 1] - 20)
    assert d1 < d0
