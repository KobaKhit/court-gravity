#!/usr/bin/env python3
"""
Matplotlib storyboard renderer — fallback when ManimCE cannot be installed
(e.g. missing MSVC / no moderngl wheels for the active Python).

Produces PNG frames + optional MP4 for the §7 narrative beats.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.archetypes import default_lineup, lineup_as_agents, make_player
from core.court import load_court_config
from core.field import FieldMode, Player, evaluate_grid, integrate_marble
from core.trajectories import TrajectoryConfig, simulate

OUT = ROOT / "data" / "storyboard"
COURT = load_court_config()


def _plot_surface(ax, players, mode=FieldMode.NET, title="", elev=55, azim=-55, nx=60, ny=55):
    XX, YY, Z = evaluate_grid(players, COURT, mode=mode, nx=nx, ny=ny)
    vmax = max(abs(Z.min()), abs(Z.max()), 1e-6)
    ax.clear()
    ax.set_facecolor("#111111")
    ax.plot_surface(
        XX,
        YY,
        Z,
        cmap="RdYlBu_r",
        vmin=-vmax,
        vmax=vmax,
        linewidth=0,
        antialiased=True,
        rstride=1,
        cstride=1,
        alpha=0.95,
    )
    for p in players:
        color = "#58C4DD" if p.team == "offense" else "#FC6255"
        ax.scatter([p.x], [p.y], [0.05], c=color, s=40)
    ax.set_title(title, color="white", fontsize=11)
    ax.set_xlabel("x (ft)", color="#888")
    ax.set_ylabel("y (ft)", color="#888")
    ax.set_zlabel("z", color="#888")
    ax.tick_params(colors="#888")
    ax.view_init(elev=elev, azim=azim)
    ax.set_zlim(-vmax * 1.1, vmax * 1.1)


def render_beat(name: str, players, mode=FieldMode.NET, elev=55, azim=-55) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(10, 7), facecolor="#111111")
    ax = fig.add_subplot(111, projection="3d", facecolor="#111111")
    _plot_surface(ax, players, mode=mode, title=name, elev=elev, azim=azim)
    path = OUT / f"{name}.png"
    fig.savefig(path, dpi=140, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path}")
    return path


def render_camera_tilt(players) -> None:
    """Cold-open style: top-down → tilted."""
    OUT.mkdir(parents=True, exist_ok=True)
    for i, elev in enumerate(np.linspace(90, 55, 12)):
        fig = plt.figure(figsize=(10, 7), facecolor="#111111")
        ax = fig.add_subplot(111, projection="3d", facecolor="#111111")
        _plot_surface(
            ax,
            players,
            mode=FieldMode.OFFENSE,
            title="One particle, one well",
            elev=float(elev),
            azim=-90 + i * 3,
        )
        fig.savefig(OUT / f"tilt_{i:02d}.png", dpi=110, facecolor=fig.get_facecolor())
        plt.close(fig)
    print(f"wrote tilt sequence in {OUT}")


def render_marble_path() -> None:
    players = [
        Player(x=-10, y=22, mass=1.3, sigma=5.5, team="offense", id="a"),
        Player(x=12, y=18, mass=0.8, sigma=5.0, team="offense", id="b"),
        Player(x=-8, y=20, mass=1.0, sigma=5.0, team="defense", id="d"),
    ]
    path = integrate_marble(players, start=(15.0, 30.0), steps=200, dt=0.03, damping=1.8)
    XX, YY, Z = evaluate_grid(players, COURT, mode=FieldMode.NET, nx=70, ny=65)
    vmax = max(abs(Z.min()), abs(Z.max()), 1e-6)
    fig = plt.figure(figsize=(10, 7), facecolor="#111111")
    ax = fig.add_subplot(111, projection="3d", facecolor="#111111")
    ax.plot_surface(XX, YY, Z, cmap="RdYlBu_r", vmin=-vmax, vmax=vmax, linewidth=0, alpha=0.9, rstride=1, cstride=1)
    from core.field import court_surface

    zpath = [float(court_surface(x, y, players, mode=FieldMode.NET, court=COURT)) for x, y in path]
    ax.plot(path[:, 0], path[:, 1], np.array(zpath) + 0.05, color="#49A88F", lw=2.5)
    ax.scatter([path[0, 0]], [path[0, 1]], [zpath[0] + 0.1], c="#49A88F", s=60)
    ax.set_title("Marble follows −∇z", color="white")
    ax.view_init(55, -40)
    fig.savefig(OUT / "marble.png", dpi=140, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'marble.png'}")


def render_animation_frames(n_frames: int = 24) -> None:
    agents = lineup_as_agents(COURT)
    data = simulate(agents, court=COURT, cfg=TrajectoryConfig(duration=6.0, dt=1 / 12, seed=2))
    OUT.mkdir(parents=True, exist_ok=True)
    for fi in range(n_frames):
        t = fi / n_frames * data["duration"]
        players = []
        for pdata in data["players"]:
            idx = min(int(t / data["dt"]), len(pdata["traj"]) - 1)
            _, x, y = pdata["traj"][idx]
            players.append(
                Player(
                    x=x,
                    y=y,
                    mass=pdata["stats"]["base_mass"],
                    sigma=pdata["stats"]["sigma"],
                    team=pdata["team"],
                    id=pdata["id"],
                )
            )
        fig = plt.figure(figsize=(9, 6.5), facecolor="#111111")
        ax = fig.add_subplot(111, projection="3d", facecolor="#111111")
        _plot_surface(ax, players, mode=FieldMode.NET, title=f"t={t:.1f}s", elev=55, azim=-50 - fi, nx=45, ny=40)
        fig.savefig(OUT / f"anim_{fi:03d}.png", dpi=100, facecolor=fig.get_facecolor())
        plt.close(fig)
    print(f"wrote {n_frames} animation frames")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Beat 2: one well
    render_beat(
        "01_one_well",
        [Player(0, 20, mass=1.5, sigma=5.5, team="offense", id="curry")],
        mode=FieldMode.OFFENSE,
        elev=60,
    )
    # Beat 4: sharpshooter KDE ring
    render_beat("02_sharpshooter_kde", [make_player("sharpshooter")], mode=FieldMode.OFFENSE)
    # Beat 5: superposition
    render_beat(
        "03_superposition",
        [
            make_player("sharpshooter", with_effectiveness=False),
            make_player("rim_runner", with_effectiveness=False),
        ],
        mode=FieldMode.OFFENSE,
    )
    # Beat 6–7: full lineup net
    lineup = default_lineup(COURT, with_effectiveness=False)
    for p in lineup:
        p.effectiveness = None
    render_beat("04_full_net", lineup, mode=FieldMode.NET)
    render_beat("05_offense_only", lineup, mode=FieldMode.OFFENSE)
    render_beat("06_defense_only", lineup, mode=FieldMode.DEFENSE)
    render_camera_tilt([Player(0, 20, mass=1.4, sigma=5.5, team="offense")])
    render_marble_path()
    render_animation_frames(16)
    # Disclaimer card
    (OUT / "DISCLAIMER.txt").write_text(
        "Pedagogical Gaussian / softened-potential model inspired by pitch-control "
        "and NBA Gravity framing — NOT the proprietary NBA Gravity metric.\n",
        encoding="utf-8",
    )
    print("Storyboard render complete:", OUT)


if __name__ == "__main__":
    main()
