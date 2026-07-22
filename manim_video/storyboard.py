"""
Additional Manim storyboard scenes covering remaining §7 beats.

Requires: pip install manim  (and a Python with prebuilt moderngl wheels,
typically 3.11/3.12 — not always available on 3.14 without MSVC).

Fallback: python manim_video/render_matplotlib.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manim_video.scenes import (  # re-export primary scenes
    AnimatedField,
    FullLineupScene,
    GravityCourtStatic,
    MarbleScene,
    OneWellReveal,
    SuperpositionScene,
    _player_dots,
    _surface_from_players,
)
from core.archetypes import make_player
from core.field import FieldMode, Player


class MassModulation(ThreeDScene):
    """Beat 3: deepen the well as 'gravity' / mass increases."""

    def construct(self):
        self.camera.background_color = "#111111"
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)
        mass = ValueTracker(0.6)

        def make():
            p = Player(0, 20, mass=mass.get_value(), sigma=5.5, team="offense", id="p")
            return _surface_from_players([p], mode=FieldMode.OFFENSE, resolution=(36, 36))

        surf = always_redraw(make)
        eq = MathTex(r"m = \mathrm{gravity}", color=YELLOW).scale(0.65).to_corner(UL)
        self.add_fixed_in_frame_mobjects(eq)
        self.add(surf)
        self.play(mass.animate.set_value(2.0), run_time=3, rate_func=smooth)
        self.wait(0.5)


class KDERingScene(ThreeDScene):
    """Beat 4: sharpshooter effectiveness ring."""

    def construct(self):
        self.camera.background_color = "#111111"
        self.set_camera_orientation(phi=55 * DEGREES, theta=-50 * DEGREES)
        p = make_player("sharpshooter", with_effectiveness=True)
        surf = _surface_from_players([p], mode=FieldMode.OFFENSE, resolution=(40, 40))
        dots = _player_dots([p])
        eq = MathTex(r"m_i(x,y)=m_i^{\mathrm{base}} g_i(x,y)", color=BLUE_B).scale(0.55)
        eq.to_corner(UL)
        self.add_fixed_in_frame_mobjects(eq)
        self.add(surf, dots)
        self.wait(2)


class DefenseInvertScene(ThreeDScene):
    """Beat 7: defense ridges vs offense wells."""

    def construct(self):
        self.camera.background_color = "#111111"
        self.set_camera_orientation(phi=60 * DEGREES, theta=-40 * DEGREES)
        off = [
            Player(-12, 22, mass=1.3, sigma=5.5, team="offense", id="a"),
            Player(10, 18, mass=1.0, sigma=5.0, team="offense", id="b"),
        ]
        de = [
            Player(-10, 20, mass=1.1, sigma=5.0, team="defense", id="d0"),
            Player(8, 16, mass=1.0, sigma=5.0, team="defense", id="d1"),
        ]
        surf = _surface_from_players(off + de, mode=FieldMode.NET, resolution=(40, 40))
        note = Tex(r"Contested space flattens", color=GREY_A).scale(0.45).to_corner(UL)
        disc = Tex(
            r"Not the NBA proprietary Gravity metric",
            color=GREY_B,
        ).scale(0.35).to_edge(DOWN)
        self.add_fixed_in_frame_mobjects(note, disc)
        self.add(surf, _player_dots(off + de))
        self.begin_ambient_camera_rotation(rate=0.07)
        self.wait(4)
        self.stop_ambient_camera_rotation()


class FlattenCoda(ThreeDScene):
    """Beat 9: flatten back toward top-down heatmap read."""

    def construct(self):
        self.camera.background_color = "#111111"
        players = [Player(0, 20, mass=1.4, sigma=5.5, team="offense", id="p")]
        surf = _surface_from_players(players, mode=FieldMode.OFFENSE, resolution=(40, 40))
        self.add(surf)
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)
        self.move_camera(phi=5 * DEGREES, theta=-90 * DEGREES, run_time=3)
        coda = Tex(r"Open the interactive web toy →", color=TEAL).scale(0.5)
        coda.to_edge(DOWN)
        self.add_fixed_in_frame_mobjects(coda)
        self.play(FadeIn(coda))
        self.wait(1)
