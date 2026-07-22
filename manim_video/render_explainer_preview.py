#!/usr/bin/env python3
"""Render a lightweight animated preview of the full explainer.

This is an **abbreviated 6-beat story reel** for motion/story review only.
It is not a 1:1 stand-in for the 12-block Manim film in ``full_explainer.py``.

    .venv\\Scripts\\python.exe manim_video\\render_explainer_preview.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.archetypes import default_lineup
from core.court import load_court_config
from core.field import FieldMode, Player, court_surface, evaluate_grid


COURT = load_court_config()
OUT = ROOT / "data" / "storyboard" / "court_gravity_explainer_preview.gif"
BG = "#04070B"
WOOD = "#5A3C25"
BLUE = "#35DFFF"
BLUE_DEEP = "#073A63"
RED = "#FF4B35"
RED_DEEP = "#691B1D"
NEUTRAL = "#151A20"
TEXT = "#EEF7FC"
MUTED = "#8395A3"

FIELD_CMAP = LinearSegmentedColormap.from_list(
    "court_gravity",
    [BLUE_DEEP, "#168EC1", "#91EFFF", NEUTRAL, "#FF9B84", RED, RED_DEEP],
    N=256,
)


def ease(value: float) -> float:
    value = float(np.clip(value, 0.0, 1.0))
    return value * value * (3.0 - 2.0 * value)


def field_state(chapter: int, progress: float) -> tuple[list[Player], str, str, str, float, float]:
    p = ease(progress)
    if chapter == 0:
        mass = 0.05 + 1.5 * p
        players = [Player(0, 23, mass=mass, sigma=5.4, team="offense", id="LUKA")]
        return (
            players,
            "Every player changes the geometry.",
            "A flat court becomes a field of spatial influence.",
            "SPACE IS NOT FLAT",
            88 - p * 34,
            -90 + p * 34,
        )

    if chapter == 1:
        sigma = 3.2 + 4.2 * p
        mass = 0.7 + 1.15 * p
        players = [Player(0, 23, mass=mass, sigma=sigma, team="offense", id="LUKA")]
        return (
            players,
            "Strength creates depth. Skill creates reach.",
            "Mass controls amplitude; σ controls how far the defense must care.",
            f"I(x,y) = m exp(−d²/2σ²)     m={mass:.2f}×   σ={sigma:.1f} ft",
            54,
            -56,
        )

    if chapter == 2:
        distance = 11 - 8.7 * p
        offense = Player(-4, 23, mass=1.5, sigma=5.8, team="offense", id="O")
        defense = Player(-4 + distance, 23, mass=1.25, sigma=5.2, team="defense", id="D")
        label = "CONTESTED SPACE FLATTENS" if distance < 4 else "OFFENSIVE ADVANTAGE"
        return (
            [offense, defense],
            "Defense pushes back.",
            "Red pressure cancels blue opportunity locally—not globally.",
            f"Z = Σ defense − Σ offense     separation={distance:.1f} ft   ·   {label}",
            56,
            -48,
        )

    if chapter == 3:
        distance = 2.3 + 7.5 * p
        offense = Player(-5, 23, mass=1.55, sigma=6.0, team="offense", id="O")
        defense = Player(-5 + distance, 23, mass=1.2, sigma=5.1, team="defense", id="D")
        return (
            [offense, defense],
            "Opportunity appears continuously.",
            "As the closeout loses distance, the blue basin rebuilds.",
            f"DEFENDER DISTANCE {distance:.1f} FT   ·   {'OPEN LOOK' if distance > 6.5 else 'DEVELOPING'}",
            58 - p * 5,
            -50 - p * 12,
        )

    if chapter == 4:
        shooter = Player(17, 25, mass=1.35 + 0.65 * p, sigma=5.8 + p, team="offense", id="SG")
        teammate = Player(10 - 24 * p, 22 - 5 * p, mass=0.9, sigma=4.8, team="offense", id="T")
        defender = Player(20 + 4 * p, 24 - 6 * p, mass=1.12, sigma=5.1, team="defense", id="D")
        helper = Player(1, 14 - 3 * p, mass=1.05, sigma=5.0, team="defense", id="H")
        return (
            [shooter, teammate, defender, helper],
            "Open is not enough.",
            "The model rewards defender separation only when teammates preserve the floor.",
            f"SPACING QUALITY {round(24 + 76 * p):02d}%   ·   {'OPEN 3' if p > 0.72 else 'VALUE SUPPRESSED'}",
            58,
            -54,
        )

    lineup = default_lineup(COURT, with_effectiveness=False)
    for player in lineup:
        player.effectiveness = None
    amount = 0.15 + 0.85 * p
    players = [replace(player, mass=player.mass * amount) for player in lineup]
    return (
        players,
        "Watch the geometry, not only the ball.",
        "Ten players superpose into one changing map of advantage.",
        f"LIVE POSSESSION   ·   FIELD {round(amount * 100):02d}%   ·   NET ADVANTAGE",
        64 - 10 * p,
        -70 + 22 * p,
    )


def draw_court(ax, z: float = 0.04) -> None:
    x0, x1 = COURT.x_extent
    y0, y1 = COURT.y_extent
    color = (0.88, 0.91, 0.93, 0.45)
    ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], [z] * 5, color=color, lw=0.9)
    ax.plot([-8, 8, 8, -8, -8], [0, 0, 19, 19, 0], [z] * 5, color=color, lw=0.8)
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(6 * np.cos(theta), 19 + 6 * np.sin(theta), np.full_like(theta, z), color=color, lw=0.7)
    theta = np.linspace(0.05 * np.pi, 0.95 * np.pi, 120)
    ax.plot(23.75 * np.cos(theta), 4 + 23.75 * np.sin(theta), np.full_like(theta, z), color=color, lw=0.8)
    ax.scatter([0], [4], [z + 0.03], s=11, color="#FF8C32", depthshade=False)


def render(output: Path, frames: int, fps: int, dpi: int) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(12.8, 7.2), facecolor=BG)
    ax = fig.add_axes([0.05, 0.08, 0.9, 0.78], projection="3d", facecolor=BG)
    title = fig.text(0.055, 0.925, "", color=TEXT, fontsize=23, fontweight="bold", ha="left", va="top")
    subtitle = fig.text(0.055, 0.875, "", color=MUTED, fontsize=10.5, ha="left", va="top")
    formula = fig.text(
        0.055,
        0.035,
        "",
        color=BLUE,
        fontsize=9.5,
        fontfamily="monospace",
        ha="left",
        va="bottom",
    )
    brand = fig.text(
        0.945,
        0.93,
        "COURT  GRAVITY",
        color="#B9C7D1",
        fontsize=9,
        fontweight="bold",
        ha="right",
        va="top",
    )
    _ = brand

    chapter_count = 6
    segment_frames = max(1, frames // chapter_count)

    def update(frame: int):
        chapter = min(chapter_count - 1, frame // segment_frames)
        local = (frame % segment_frames) / max(1, segment_frames - 1)
        players, heading, copy, readout, elev, azim = field_state(chapter, local)
        XX, YY, Z = evaluate_grid(players, COURT, mode=FieldMode.NET, nx=52, ny=46)
        vmax = max(float(abs(Z.min())), float(abs(Z.max())), 0.4)

        ax.clear()
        ax.set_facecolor(BG)
        ax.plot_surface(
            XX,
            YY,
            Z,
            cmap=FIELD_CMAP,
            vmin=-vmax,
            vmax=vmax,
            linewidth=0,
            antialiased=True,
            rcount=46,
            ccount=52,
            alpha=0.97,
            shade=True,
        )
        levels = np.linspace(-vmax * 0.82, vmax * 0.82, 9)
        ax.contour(
            XX,
            YY,
            Z,
            levels=levels,
            cmap=FIELD_CMAP,
            vmin=-vmax,
            vmax=vmax,
            linewidths=0.55,
            alpha=0.48,
        )
        draw_court(ax)

        for player in players:
            z = float(court_surface(player.x, player.y, players, mode=FieldMode.NET, court=COURT))
            color = BLUE if player.team == "offense" else RED
            ax.scatter([player.x], [player.y], [z + 0.17], color=color, s=44, edgecolor="white", linewidth=0.5, depthshade=False)
            if len(players) <= 4:
                ax.text(player.x, player.y, z + 0.34, player.id, color="white", fontsize=7, ha="center", va="center")

        x0, x1 = COURT.x_extent
        y0, y1 = COURT.y_extent
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_zlim(-vmax * 1.12, vmax * 1.12)
        ax.set_box_aspect((50, 47, 17))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.grid(False)

        title.set_text(heading)
        subtitle.set_text(copy)
        formula.set_text(f"{chapter + 1:02d} / {chapter_count:02d}     {readout}")
        return title, subtitle, formula

    animation = FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=False)
    animation.save(output, writer=PillowWriter(fps=fps), dpi=dpi)
    plt.close(fig)
    print(f"Wrote animated explainer preview: {output}")
    return output


def encode_mp4(gif_path: Path, mp4_path: Path) -> Path:
    """Convert the review GIF to a broadly compatible H.264 MP4."""
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "MP4 output requires imageio-ffmpeg. Install the preview extra: "
            'pip install -e ".[preview]"'
        ) from exc

    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-y",
        "-i",
        str(gif_path),
        "-vf",
        "fps=24,scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4_path),
    ]
    subprocess.run(command, check=True, capture_output=True)
    print(f"Wrote MP4 explainer preview: {mp4_path}")
    return mp4_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--frames", type=int, default=72)
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--dpi", type=int, default=80)
    parser.add_argument("--mp4", type=Path, default=None, help="Optionally encode the rendered GIF as H.264 MP4")
    args = parser.parse_args()
    gif_path = render(args.output, max(24, args.frames), max(2, args.fps), max(50, args.dpi))
    if args.mp4 is not None:
        encode_mp4(gif_path, args.mp4)


if __name__ == "__main__":
    main()
