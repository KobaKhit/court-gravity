"""Manim Community scenes for the Court Gravity explainer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.archetypes import default_lineup, make_player
from core.court import load_court_config
from core.field import FieldMode, Player, court_surface, integrate_marble


COURT = load_court_config()
SCALE = 0.12  # feet → Manim units
# Center the half-court at the origin so angled cameras frame it evenly.
X_CENTER = 0.5 * sum(COURT.x_extent)
Y_CENTER = 0.5 * sum(COURT.y_extent)


def _to_scene(x: float, y: float, z: float = 0.0) -> np.ndarray:
    return np.array([(x - X_CENTER) * SCALE, (y - Y_CENTER) * SCALE, z * SCALE])


def _surface_from_players(
    players: list[Player],
    *,
    mode: FieldMode = FieldMode.NET,
    resolution: tuple[int, int] = (40, 40),
    z_scale: float = 1.0,
    fill_opacity: float = 0.92,
    stroke_opacity: float = 0.14,
) -> Surface:
    if os.environ.get("COURT_GRAVITY_DRAFT") == "1":
        resolution = (min(resolution[0], 20), min(resolution[1], 16))
    x0, x1 = COURT.x_extent
    y0, y1 = COURT.y_extent

    def func(u: float, v: float) -> np.ndarray:
        z = float(court_surface(u, v, players, mode=mode, court=COURT)) * z_scale
        return _to_scene(u, v, z)

    surf = Surface(
        func,
        u_range=[x0, x1],
        v_range=[y0, y1],
        resolution=resolution,
        fill_opacity=fill_opacity,
        checkerboard_colors=False,
    )
    # Surface points are expressed directly in scene coordinates rather than
    # through ``ThreeDAxes.c2p``. Color each patch from its actual signed
    # height so the map remains vivid and correct across Manim versions.
    neutral = ManimColor("#151A20")
    for patch in surf:
        field_height = float(patch.get_center()[2] / SCALE)
        strength = min(1.0, abs(field_height) / 1.35)
        if field_height < -0.012:
            color = interpolate_color(neutral, BLUE_C, 0.25 + strength * 0.75)
        elif field_height > 0.012:
            color = interpolate_color(neutral, RED_C, 0.25 + strength * 0.75)
        else:
            color = neutral
        patch.set_fill(color, opacity=fill_opacity)
        patch.set_stroke(color, width=0.25, opacity=stroke_opacity)
    return surf


def _player_dots(players: list[Player]) -> VGroup:
    dots = VGroup()
    for p in players:
        color = BLUE_C if p.team == "offense" else RED_C
        d = Dot3D(point=_to_scene(p.x, p.y, 0.05), color=color, radius=0.06)
        dots.add(d)
    return dots


def _player_motion_paths(
    before: list[Player],
    after: list[Player],
    *,
    z: float = 0.08,
    dashed: bool = False,
) -> VGroup:
    """Court-projected 3D paths for players that move between two states."""
    previous = {player.id: player for player in before}
    paths = VGroup()
    for player in after:
        start = previous.get(player.id)
        if start is None or np.allclose((start.x, start.y), (player.x, player.y)):
            continue
        color = BLUE_C if player.team == "offense" else RED_C
        p0 = _to_scene(start.x, start.y, z)
        p1 = _to_scene(player.x, player.y, z)
        if dashed:
            # Short Line3D segments stay depth-correct under camera motion.
            segments = VGroup()
            steps = 10
            for i in range(0, steps, 2):
                a = p0 + (p1 - p0) * (i / steps)
                b = p0 + (p1 - p0) * ((i + 1) / steps)
                segments.add(Line3D(a, b, color=color, thickness=0.01))
            paths.add(segments)
        else:
            paths.add(Line3D(p0, p1, color=color, thickness=0.012))
    return paths


class GravityCourtStatic(ThreeDScene):
    """Phase 1: static warped court with one well."""

    def construct(self):
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES, zoom=1.2)
        self.camera.background_color = "#111111"
        players = [Player(x=0.0, y=20.0, mass=1.5, sigma=5.0, team="offense", id="p0")]
        surf = _surface_from_players(players, mode=FieldMode.OFFENSE, resolution=(50, 50))
        dots = _player_dots(players)
        eq = MathTex(r"I(x,y)=m\,e^{-r^{2}/2\sigma^{2}}", color=WHITE).scale(0.7)
        eq.to_corner(UL)
        self.add_fixed_in_frame_mobjects(eq)
        self.add(surf, dots)
        self.wait(1)


class OneWellReveal(ThreeDScene):
    """Storyboard beat: top-down → tilt to reveal well."""

    def construct(self):
        self.camera.background_color = "#111111"
        players = [Player(x=0.0, y=20.0, mass=1.4, sigma=5.5, team="offense", id="curry")]
        surf = _surface_from_players(players, mode=FieldMode.OFFENSE, resolution=(45, 45))
        dots = _player_dots(players)
        caption = Tex(r"What if a great shooter bent the floor?", color=WHITE).scale(0.5)
        caption.to_corner(UL)
        self.add_fixed_in_frame_mobjects(caption)
        self.set_camera_orientation(phi=0 * DEGREES, theta=-90 * DEGREES, zoom=1.0)
        self.add(surf, dots)
        self.wait(0.5)
        self.move_camera(phi=65 * DEGREES, theta=-50 * DEGREES, run_time=3)
        eq = MathTex(r"z=-\sum_i m_i e^{-r_i^{2}/2\sigma^{2}}", color=BLUE_B).scale(0.65)
        eq.to_corner(UR)
        self.add_fixed_in_frame_mobjects(eq)
        self.play(FadeIn(eq))
        self.wait(1)


class SuperpositionScene(ThreeDScene):
    """Two players → superposition."""

    def construct(self):
        self.camera.background_color = "#111111"
        self.set_camera_orientation(phi=60 * DEGREES, theta=-40 * DEGREES)
        p1 = make_player("sharpshooter", player_id="sg", with_effectiveness=False)
        p2 = make_player("rim_runner", player_id="c", with_effectiveness=False)
        players = [p1, p2]
        surf = _surface_from_players(players, mode=FieldMode.OFFENSE, resolution=(45, 45))
        dots = _player_dots(players)
        eq = MathTex(r"z=I_1+I_2", color=WHITE).scale(0.7).to_corner(UL)
        self.add_fixed_in_frame_mobjects(eq)
        self.add(surf, dots)
        self.begin_ambient_camera_rotation(rate=0.08)
        self.wait(4)
        self.stop_ambient_camera_rotation()


class FullLineupScene(ThreeDScene):
    """Full offense + defense signed field."""

    def construct(self):
        self.camera.background_color = "#111111"
        self.set_camera_orientation(phi=55 * DEGREES, theta=-55 * DEGREES, zoom=1.1)
        players = default_lineup(COURT, with_effectiveness=False)
        # Strip effectiveness for speed in draft renders
        for p in players:
            p.effectiveness = None
        surf = _surface_from_players(players, mode=FieldMode.NET, resolution=(40, 40), z_scale=0.8)
        dots = _player_dots(players)
        note = Tex(
            r"Pedagogical model — not the NBA proprietary Gravity metric",
            color=GREY_B,
        ).scale(0.35)
        note.to_edge(DOWN)
        self.add_fixed_in_frame_mobjects(note)
        mode_label = Tex(r"mode: net", color=YELLOW).scale(0.5).to_corner(UL)
        self.add_fixed_in_frame_mobjects(mode_label)
        self.add(surf, dots)
        self.begin_ambient_camera_rotation(rate=0.06)
        self.wait(5)
        self.stop_ambient_camera_rotation()


class MarbleScene(ThreeDScene):
    """Test marble rolls into an open well along −∇z."""

    def construct(self):
        self.camera.background_color = "#111111"
        self.set_camera_orientation(phi=70 * DEGREES, theta=-30 * DEGREES)
        players = [
            Player(x=-10, y=22, mass=1.3, sigma=5.5, team="offense", id="a"),
            Player(x=12, y=18, mass=0.8, sigma=5.0, team="offense", id="b"),
            Player(x=-8, y=20, mass=1.0, sigma=5.0, team="defense", id="d"),
        ]
        surf = _surface_from_players(players, mode=FieldMode.NET, resolution=(40, 40))
        dots = _player_dots(players)
        path = integrate_marble(players, start=(15.0, 30.0), steps=250, dt=0.025, damping=1.8)
        marble = Sphere(radius=0.08, color=TEAL).move_to(_to_scene(path[0, 0], path[0, 1], 0.15))
        self.add(surf, dots, marble)
        # Animate along subsampled path
        idxs = np.linspace(0, len(path) - 1, 60).astype(int)
        for i in idxs[1:]:
            target = _to_scene(path[i, 0], path[i, 1], 0.12)
            self.play(marble.animate.move_to(target), run_time=0.05, rate_func=linear)
        self.wait(0.5)


class AnimatedField(ThreeDScene):
    """Surface morphs as players move along synthetic trajectories."""

    def construct(self):
        self.camera.background_color = "#111111"
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        from core.archetypes import lineup_as_agents
        from core.trajectories import TrajectoryConfig, simulate

        agents = lineup_as_agents(COURT)
        data = simulate(agents, court=COURT, cfg=TrajectoryConfig(duration=6.0, dt=1 / 15, seed=2))

        t_tracker = ValueTracker(0.0)

        def players_at(t: float) -> list[Player]:
            out = []
            for pdata in data["players"]:
                traj = pdata["traj"]
                # nearest frame
                idx = min(int(t / data["dt"]), len(traj) - 1)
                _, x, y = traj[idx]
                out.append(
                    Player(
                        x=x,
                        y=y,
                        mass=pdata["stats"]["base_mass"],
                        sigma=pdata["stats"]["sigma"],
                        team=pdata["team"],
                        id=pdata["id"],
                    )
                )
            return out

        def make_surf():
            return _surface_from_players(
                players_at(t_tracker.get_value()),
                mode=FieldMode.NET,
                resolution=(32, 32),
                z_scale=0.7,
            )

        surf = always_redraw(make_surf)
        self.add(surf)
        self.play(t_tracker.animate.set_value(5.5), run_time=6, rate_func=linear)
        self.wait(0.3)
