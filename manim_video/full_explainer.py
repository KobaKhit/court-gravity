"""A continuous educational Court Gravity film.

Render a draft:
    manim -ql manim_video/full_explainer.py CourtGravityExplainer

Render the final:
    manim -qk --fps 60 --renderer=opengl \
        manim_video/full_explainer.py CourtGravityExplainer

The scene deliberately uses ``Text`` rather than LaTeX-backed mobjects so the
first render only needs Manim, Pango, and FFmpeg.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
from manim import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.archetypes import default_lineup
from core.field import FieldMode, Player
from manim_video.scenes import COURT, SCALE, _player_dots, _surface_from_players, _to_scene


BG = "#04070B"
WOOD = "#5B3B22"
BLUE = "#43DFFF"
BLUE_SOFT = "#7BEAFF"
RED = "#FF4B35"
MUTED = "#8495A3"
WHITE_SOFT = "#EAF4FA"


def smoothstep(value: float) -> float:
    value = float(np.clip(value, 0.0, 1.0))
    return value * value * (3.0 - 2.0 * value)


def scaled_players(players: list[Player], amount: float) -> list[Player]:
    return [replace(player, mass=player.mass * amount, effectiveness=None) for player in players]


def court_lines() -> VGroup:
    """Minimal court geometry kept at the neutral z plane."""
    line_color = GREY_B
    z = 0.025
    x0, x1 = COURT.x_extent
    y0, y1 = COURT.y_extent
    group = VGroup()

    outline = Polygon(
        _to_scene(x0, y0, z),
        _to_scene(x1, y0, z),
        _to_scene(x1, y1, z),
        _to_scene(x0, y1, z),
        color=line_color,
        stroke_width=1.6,
    )
    paint = Polygon(
        _to_scene(-8, 0, z),
        _to_scene(8, 0, z),
        _to_scene(8, 19, z),
        _to_scene(-8, 19, z),
        color=line_color,
        stroke_width=1.2,
    )
    free_throw = ParametricFunction(
        lambda t: _to_scene(6 * np.cos(t), 19 + 6 * np.sin(t), z),
        t_range=[0, TAU],
        color=line_color,
        stroke_width=1.2,
    )
    rim = ParametricFunction(
        lambda t: _to_scene(0.75 * np.cos(t), 4 + 0.75 * np.sin(t), z),
        t_range=[0, TAU],
        color=ORANGE,
        stroke_width=2,
    )
    arc = ParametricFunction(
        lambda t: _to_scene(23.75 * np.cos(t), 4 + 23.75 * np.sin(t), z),
        t_range=[0.04 * PI, 0.96 * PI],
        color=line_color,
        stroke_width=1.2,
    )
    center = Line3D(_to_scene(x0, y1, z), _to_scene(x1, y1, z), color=line_color, thickness=0.008)
    group.add(outline, paint, free_throw, rim, arc, center)
    group.set_opacity(0.52)
    return group


def contour_rings(player: Player, color: str, count: int = 4) -> VGroup:
    rings = VGroup()
    for index in range(1, count + 1):
        radius = player.sigma * SCALE * (0.42 + index * 0.34)
        ring = Circle(radius=radius, color=color, stroke_width=1.3)
        ring.move_to(_to_scene(player.x, player.y, 0.05))
        ring.set_opacity(0.58 - index * 0.08)
        rings.add(ring)
    return rings


class CourtGravityExplainer(ThreeDScene):
    """A roughly four-minute visual cut, paced for the narration script."""

    def construct(self):
        self.camera.background_color = BG
        self.set_camera_orientation(phi=3 * DEGREES, theta=-90 * DEGREES, zoom=1.08)

        self._cold_open()
        self._single_kernel()
        self._mass_and_radius()
        self._contours_and_views()
        self._ratings()
        self._cancellation()
        self._superposition_breakdown()
        self._spacing()
        self._lifecycle()
        self._live_possession()
        self._counterfactual()
        self._coda()

    def chapter_card(self, number: str, title: str, body: str, *, accent: str = BLUE) -> VGroup:
        eyebrow = Text(number, font="Segoe UI", font_size=20, weight="BOLD", color=accent)
        heading = Text(title, font="Segoe UI", font_size=42, weight="BOLD", color=WHITE_SOFT)
        copy = Text(body, font="Segoe UI", font_size=20, color=MUTED, line_spacing=0.8)
        card = VGroup(eyebrow, heading, copy).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
        card.to_corner(UL, buff=0.38)
        self.add_fixed_in_frame_mobjects(card)
        return card

    def formula(self, text: str, color: str = WHITE_SOFT) -> VGroup:
        label = Text(text, font="Consolas", font_size=25, color=color)
        panel = SurroundingRectangle(label, buff=0.18, color=GREY_D, stroke_width=1)
        panel.set_fill(BG, opacity=0.82)
        group = VGroup(panel, label).to_corner(UR, buff=0.38)
        self.add_fixed_in_frame_mobjects(group)
        return group

    def fixed_badge(self, text: str, color: str, *, register: bool = True) -> VGroup:
        label = Text(text, font="Segoe UI", font_size=18, weight="BOLD", color=color)
        panel = SurroundingRectangle(label, buff=0.13, color=color, stroke_width=1)
        panel.set_fill(BG, opacity=0.88)
        badge = VGroup(panel, label).to_edge(DOWN, buff=0.3)
        if register:
            self.add_fixed_in_frame_mobjects(badge)
        return badge

    def _cold_open(self):
        title = Text("COURT", font="Segoe UI", font_size=76, weight="BOLD", color=WHITE)
        gravity = Text("GRAVITY", font="Segoe UI", font_size=76, weight="LIGHT", color=BLUE_SOFT)
        lockup = VGroup(title, gravity).arrange(RIGHT, buff=0.18)
        subtitle = Text(
            "Every player changes the geometry of a possession.",
            font="Segoe UI",
            font_size=25,
            color=MUTED,
        )
        intro = VGroup(lockup, subtitle).arrange(DOWN, buff=0.22)
        self.add_fixed_in_frame_mobjects(intro)

        self.play(Write(title), FadeIn(gravity, shift=RIGHT * 0.2), run_time=1.8)
        self.play(FadeIn(subtitle, shift=UP * 0.12), run_time=0.8)
        self.wait(2.2)
        self.play(FadeOut(intro), run_time=0.8)

        player = Player(0, 24, mass=0.0, sigma=5.5, team="offense", id="Luka")
        flat = _surface_from_players([], mode=FieldMode.NET, resolution=(42, 36), z_scale=1.15)
        lines = court_lines()
        dot = _player_dots([replace(player, mass=1.45)])
        self.add(flat, lines)
        self.play(FadeIn(dot, scale=0.5), run_time=0.7)

        well = _surface_from_players(
            [replace(player, mass=1.45)],
            mode=FieldMode.OFFENSE,
            resolution=(42, 36),
            z_scale=1.15,
        )
        self.play(Transform(flat, well), run_time=2.4, rate_func=smooth)
        self.move_camera(phi=62 * DEGREES, theta=-50 * DEGREES, zoom=1.13, run_time=3.0)

        hook = self.fixed_badge("SPACE IS NOT FLAT", BLUE)
        self.play(FadeIn(hook, shift=UP * 0.1), run_time=0.5)
        self.wait(2.4)
        self.play(FadeOut(hook), FadeOut(flat), FadeOut(lines), FadeOut(dot), run_time=0.8)

    def _single_kernel(self):
        self.next_section("one-player-one-field")
        player = Player(0, 23, mass=1.35, sigma=5.2, team="offense", id="Luka")
        surface = _surface_from_players([player], mode=FieldMode.OFFENSE, resolution=(44, 38), z_scale=1.2)
        dots = _player_dots([player])
        rings = contour_rings(player, BLUE)
        lines = court_lines()
        card = self.chapter_card(
            "01 · THE KERNEL",
            "One player. One field.",
            "Location sets the center. Mass sets depth. Radius sets reach.",
        )
        eq = self.formula("I(x, y) = m · exp(−d² / 2σ²)", BLUE_SOFT)

        self.add(surface, lines, dots)
        self.play(FadeIn(card), FadeIn(eq), LaggedStart(*[Create(ring) for ring in rings], lag_ratio=0.16), run_time=2)
        self.begin_ambient_camera_rotation(rate=0.035)
        self.wait(8.5)
        self.stop_ambient_camera_rotation()
        self.play(FadeOut(card), FadeOut(eq), FadeOut(rings), FadeOut(surface), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _mass_and_radius(self):
        self.next_section("mass-and-radius")
        base = Player(0, 23, mass=0.55, sigma=4.2, team="offense", id="Luka")
        surface = _surface_from_players([base], mode=FieldMode.OFFENSE, resolution=(44, 38), z_scale=1.2)
        lines = court_lines()
        dot = _player_dots([base])
        card = self.chapter_card(
            "02 · STRENGTH + REACH",
            "Great players bend more space.",
            "Production changes influence strength; role and skill change its radius.",
        )
        readout = self.fixed_badge("MASS  0.55×    ·    RADIUS  4.2 FT", BLUE)
        self.add(surface, lines, dot)
        self.play(FadeIn(card), FadeIn(readout), run_time=0.8)

        heavy = replace(base, mass=1.85)
        heavy_surface = _surface_from_players([heavy], mode=FieldMode.OFFENSE, resolution=(44, 38), z_scale=1.2)
        heavy_readout = self.fixed_badge("MASS  1.85×    ·    RADIUS  4.2 FT", BLUE, register=False)
        self.play(Transform(surface, heavy_surface), Transform(readout, heavy_readout), run_time=2.8, rate_func=smooth)
        self.wait(0.6)

        broad = replace(heavy, sigma=7.2)
        broad_surface = _surface_from_players([broad], mode=FieldMode.OFFENSE, resolution=(44, 38), z_scale=1.2)
        broad_readout = self.fixed_badge("MASS  1.85×    ·    RADIUS  7.2 FT", BLUE, register=False)
        rings = contour_rings(broad, BLUE)
        self.play(
            Transform(surface, broad_surface),
            Transform(readout, broad_readout),
            LaggedStart(*[Create(ring) for ring in rings], lag_ratio=0.12),
            run_time=2.8,
            rate_func=smooth,
        )
        self.wait(1.2)
        self.wait(6.0)
        self.play(FadeOut(card), FadeOut(readout), FadeOut(rings), FadeOut(surface), FadeOut(lines), FadeOut(dot), run_time=0.9)

    def _contours_and_views(self):
        self.next_section("topology-to-weather-map")
        player = Player(-4, 23, mass=1.6, sigma=6.3, team="offense", id="O")
        defender = Player(8, 19, mass=1.15, sigma=5.1, team="defense", id="D")
        players = [player, defender]
        surface = _surface_from_players(players, mode=FieldMode.NET, resolution=(46, 40), z_scale=1.08)
        lines = court_lines()
        dots = _player_dots(players)
        rings = VGroup(contour_rings(player, BLUE, count=5), contour_rings(defender, RED, count=4))
        card = self.chapter_card(
            "03 · TWO VIEWS",
            "Topology and heatmap are the same model.",
            "Height communicates advantage. Contours project that shape back onto the court.",
        )
        badge = self.fixed_badge("ANGLED VIEW  ·  TOPOLOGY", BLUE)
        self.set_camera_orientation(phi=62 * DEGREES, theta=-52 * DEGREES, zoom=1.08)
        self.add(surface, lines, dots)
        self.play(FadeIn(card), FadeIn(badge), LaggedStart(*[Create(ring) for ring in rings], lag_ratio=0.08), run_time=2.2)
        self.begin_ambient_camera_rotation(rate=0.025)
        self.wait(4.5)
        self.stop_ambient_camera_rotation()

        top_badge = self.fixed_badge("TOP DOWN  ·  WEATHER MAP", BLUE, register=False)
        self.play(
            Transform(badge, top_badge),
            self.camera.phi_tracker.animate.set_value(5 * DEGREES),
            self.camera.theta_tracker.animate.set_value(-90 * DEGREES),
            run_time=3.5,
            rate_func=smooth,
        )
        self.wait(6.5)
        self.play(
            self.camera.phi_tracker.animate.set_value(58 * DEGREES),
            self.camera.theta_tracker.animate.set_value(-48 * DEGREES),
            run_time=3.0,
            rate_func=smooth,
        )
        self.wait(2.8)
        self.play(FadeOut(card), FadeOut(badge), FadeOut(rings), FadeOut(surface), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _ratings(self):
        self.next_section("ratings-to-gravity")
        self.set_camera_orientation(phi=5 * DEGREES, theta=-90 * DEGREES, zoom=1.0)
        card = self.chapter_card(
            "04 · PLAYER RATINGS",
            "The field starts with the player.",
            "Season production establishes a baseline; live context determines its value now.",
        )

        def rating_card(name: str, subtitle: str, offense: float, defense: float, color: str) -> VGroup:
            name_text = Text(name, font="Segoe UI", font_size=28, weight="BOLD", color=WHITE_SOFT)
            sub_text = Text(subtitle, font="Segoe UI", font_size=15, color=MUTED)
            offense_label = Text(f"OFFENSE  {offense:.2f}×", font="Consolas", font_size=17, color=BLUE)
            defense_label = Text(f"DEFENSE  {defense:.2f}×", font="Consolas", font_size=17, color=RED)
            offense_bg = Rectangle(width=3.0, height=0.09, fill_color=GREY_E, fill_opacity=0.5, stroke_width=0)
            offense_bar = Rectangle(
                width=3.0 * offense / 1.6,
                height=0.09,
                fill_color=BLUE,
                fill_opacity=1,
                stroke_width=0,
            ).align_to(offense_bg, LEFT)
            defense_bg = Rectangle(width=3.0, height=0.09, fill_color=GREY_E, fill_opacity=0.5, stroke_width=0)
            defense_bar = Rectangle(
                width=3.0 * defense / 1.6,
                height=0.09,
                fill_color=RED,
                fill_opacity=1,
                stroke_width=0,
            ).align_to(defense_bg, LEFT)
            offense_row = VGroup(offense_label, VGroup(offense_bg, offense_bar)).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
            defense_row = VGroup(defense_label, VGroup(defense_bg, defense_bar)).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
            content = VGroup(name_text, sub_text, offense_row, defense_row).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
            panel = SurroundingRectangle(content, buff=0.25, color=color, stroke_width=1.2)
            panel.set_fill("#071019", opacity=0.9)
            return VGroup(panel, content)

        luka = rating_card("Luka Dončić", "LAL · PG · 2025–26 profile", 1.47, 0.86, BLUE)
        wemby = rating_card("Victor Wembanyama", "SAS · C · 2025–26 profile", 1.17, 1.54, RED)
        comparison = VGroup(luka, wemby).arrange(RIGHT, buff=0.45).shift(DOWN * 0.35)
        self.add_fixed_in_frame_mobjects(comparison)
        self.play(FadeIn(card), LaggedStart(FadeIn(luka, shift=RIGHT * 0.25), FadeIn(wemby, shift=LEFT * 0.25), lag_ratio=0.35), run_time=1.8)
        self.wait(8.0)

        formula = self.formula("baseline × role × location × live context", WHITE_SOFT)
        self.play(FadeIn(formula), run_time=0.6)
        self.wait(5.5)
        self.play(FadeOut(comparison), run_time=0.8)

        players = [
            Player(-12, 23, mass=1.47, sigma=6.5, team="offense", id="LUKA"),
            Player(11, 18, mass=1.54, sigma=6.2, team="defense", id="WEMBY"),
        ]
        surface = _surface_from_players(players, mode=FieldMode.NET, resolution=(46, 40), z_scale=1.0)
        lines = court_lines()
        dots = _player_dots(players)
        self.add(surface, lines, dots)
        self.move_camera(phi=58 * DEGREES, theta=-50 * DEGREES, run_time=2.8)
        self.wait(5.5)
        self.play(FadeOut(card), FadeOut(formula), FadeOut(surface), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _cancellation(self):
        self.next_section("defensive-cancellation")
        offense = Player(-5, 23, mass=1.4, sigma=5.8, team="offense", id="O")
        defender_far = Player(9, 23, mass=1.2, sigma=5.2, team="defense", id="D")
        players = [offense, defender_far]
        surface = _surface_from_players(players, mode=FieldMode.NET, resolution=(46, 40), z_scale=1.1)
        dots = _player_dots(players)
        lines = court_lines()
        card = self.chapter_card(
            "05 · NET ADVANTAGE",
            "Defense pushes back.",
            "Blue wells and red ridges are compared at every point on the floor.",
            accent=RED,
        )
        eq = self.formula("Z = Σ defense − Σ offense", WHITE_SOFT)
        badge = self.fixed_badge("9.0 FT  ·  OFFENSIVE ADVANTAGE", BLUE)
        self.add(surface, lines, dots)
        self.play(FadeIn(card), FadeIn(eq), FadeIn(badge), run_time=1)
        self.wait(4.2)

        defender_close = replace(defender_far, x=-2.4)
        contested = [offense, defender_close]
        contested_surface = _surface_from_players(contested, mode=FieldMode.NET, resolution=(46, 40), z_scale=1.1)
        contested_dots = _player_dots(contested)
        contested_badge = self.fixed_badge("2.6 FT  ·  CONTESTED SPACE FLATTENS", GREY_A, register=False)
        self.play(
            Transform(surface, contested_surface),
            Transform(dots, contested_dots),
            Transform(badge, contested_badge),
            run_time=3.2,
            rate_func=smooth,
        )
        self.wait(4.6)

        defender_late = replace(defender_far, x=6.5)
        open_players = [offense, defender_late]
        open_surface = _surface_from_players(open_players, mode=FieldMode.NET, resolution=(46, 40), z_scale=1.1)
        open_dots = _player_dots(open_players)
        open_badge = self.fixed_badge("7.4 FT  ·  THE BLUE BASIN REAPPEARS", BLUE, register=False)
        self.play(
            Transform(surface, open_surface),
            Transform(dots, open_dots),
            Transform(badge, open_badge),
            run_time=3.0,
            rate_func=smooth,
        )
        self.wait(4.2)
        self.play(FadeOut(card), FadeOut(eq), FadeOut(badge), FadeOut(surface), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _superposition_breakdown(self):
        self.next_section("full-lineup-superposition")
        lineup = default_lineup(COURT, with_effectiveness=False)
        offense = [player for player in lineup if player.team == "offense"]
        defense = [player for player in lineup if player.team == "defense"]
        surface = _surface_from_players(offense, mode=FieldMode.OFFENSE, resolution=(42, 36), z_scale=0.82)
        lines = court_lines()
        dots = _player_dots(offense)
        card = self.chapter_card(
            "06 · SUPERPOSITION",
            "Ten fields become one possession.",
            "The model adds every responsibility before it asks which side owns the space.",
        )
        formula = self.formula("Z(x,y) = −Σ offense + Σ defense", WHITE_SOFT)
        badge = self.fixed_badge("LAYER 1  ·  OFFENSIVE PRESSURE", BLUE)
        self.add(surface, lines, dots)
        self.play(FadeIn(card), FadeIn(formula), FadeIn(badge), run_time=1.0)
        self.wait(5.0)

        defense_surface = _surface_from_players(defense, mode=FieldMode.DEFENSE, resolution=(42, 36), z_scale=0.82)
        defense_dots = _player_dots(defense)
        defense_badge = self.fixed_badge("LAYER 2  ·  DEFENSIVE PRESSURE", RED, register=False)
        self.play(
            Transform(surface, defense_surface),
            Transform(dots, defense_dots),
            Transform(badge, defense_badge),
            run_time=3.5,
            rate_func=smooth,
        )
        self.wait(5.0)

        net_surface = _surface_from_players(lineup, mode=FieldMode.NET, resolution=(42, 36), z_scale=0.82)
        net_dots = _player_dots(lineup)
        net_badge = self.fixed_badge("LAYER 3  ·  NET ADVANTAGE", WHITE_SOFT, register=False)
        self.play(
            Transform(surface, net_surface),
            Transform(dots, net_dots),
            Transform(badge, net_badge),
            run_time=4.0,
            rate_func=smooth,
        )
        self.begin_ambient_camera_rotation(rate=0.028)
        self.wait(7.0)
        self.stop_ambient_camera_rotation()
        self.wait(2.0)
        self.play(FadeOut(card), FadeOut(formula), FadeOut(badge), FadeOut(surface), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _spacing(self):
        self.next_section("spacing-and-floor-balance")
        shooter = Player(15, 24, mass=1.45, sigma=6.0, team="offense", id="S")
        teammate_crowded = Player(10, 23, mass=1.0, sigma=5.0, team="offense", id="T")
        defender = Player(20, 24, mass=1.12, sigma=5.2, team="defense", id="D")
        crowded = [shooter, teammate_crowded, defender]
        surface = _surface_from_players(crowded, mode=FieldMode.NET, resolution=(46, 40), z_scale=1.0)
        dots = _player_dots(crowded)
        lines = court_lines()
        card = self.chapter_card(
            "07 · SPACING",
            "Open is not enough.",
            "A useful advantage also requires teammates to preserve the shape of the floor.",
        )
        badge = self.fixed_badge("DEFENDER 5.0 FT  ·  TEAMMATE 5.1 FT  ·  VALUE SUPPRESSED", GREY_A)
        self.add(surface, lines, dots)
        self.play(FadeIn(card), FadeIn(badge), run_time=0.9)
        self.wait(4.6)

        teammate_spaced = replace(teammate_crowded, x=-4, y=17)
        defender_lost = replace(defender, x=24.5, y=18)
        balanced = [replace(shooter, mass=1.75, sigma=6.5), teammate_spaced, defender_lost]
        balanced_surface = _surface_from_players(balanced, mode=FieldMode.NET, resolution=(46, 40), z_scale=1.0)
        balanced_dots = _player_dots(balanced)
        balanced_badge = self.fixed_badge(
            "DEFENDER 8.5 FT  ·  TEAMMATE 20+ FT  ·  OPEN 3",
            BLUE,
            register=False,
        )
        rings = contour_rings(balanced[0], BLUE, count=5)
        self.play(
            Transform(surface, balanced_surface),
            Transform(dots, balanced_dots),
            Transform(badge, balanced_badge),
            LaggedStart(*[Create(ring) for ring in rings], lag_ratio=0.1),
            run_time=3.5,
            rate_func=smooth,
        )
        self.wait(6.2)
        self.play(FadeOut(card), FadeOut(badge), FadeOut(rings), FadeOut(surface), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _lifecycle(self):
        self.next_section("possession-lifecycle")
        lineup = default_lineup(COURT, with_effectiveness=False)
        lines = court_lines()
        flat = _surface_from_players([], mode=FieldMode.NET, resolution=(42, 36), z_scale=0.8)
        card = self.chapter_card(
            "08 · GAME STATE",
            "The topology breathes with the ball.",
            "Dead ball: zero. Inbound: rebuild. Action: full live pressure.",
        )
        badge = self.fixed_badge("DEAD BALL  ·  FIELD 0%", GREY_A)
        self.add(flat, lines)
        self.play(FadeIn(card), FadeIn(badge), run_time=0.8)
        self.wait(3.8)

        dots = _player_dots(lineup)
        self.play(FadeIn(dots, scale=0.75), run_time=0.8)
        for amount, label in [
            (0.18, "INBOUND  ·  FIELD 18%"),
            (0.48, "TRANSITION  ·  FIELD 48%"),
            (0.78, "SET  ·  FIELD 78%"),
            (1.0, "ACTION  ·  FIELD 100%"),
        ]:
            target = _surface_from_players(
                scaled_players(lineup, amount),
                mode=FieldMode.NET,
                resolution=(42, 36),
                z_scale=0.8,
            )
            target_badge = self.fixed_badge(label, BLUE if amount > 0.5 else GREY_A, register=False)
            self.play(Transform(flat, target), Transform(badge, target_badge), run_time=1.35, rate_func=smooth)
            self.wait(1.2)
        self.wait(4.2)
        self.play(FadeOut(card), FadeOut(badge), FadeOut(flat), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _live_possession(self):
        self.next_section("live-possession")
        lineup = default_lineup(COURT, with_effectiveness=False)
        surface = _surface_from_players(lineup, mode=FieldMode.NET, resolution=(40, 34), z_scale=0.78)
        dots = _player_dots(lineup)
        lines = court_lines()
        card = self.chapter_card(
            "09 · THE POSSESSION",
            "Watch the geometry, not the ball.",
            "A drive compresses the defense. The weak side inherits the space.",
        )
        badge = self.fixed_badge("HORNS KICKOUT  ·  SET", GREY_A)
        self.add(surface, lines, dots)
        self.play(FadeIn(card), FadeIn(badge), run_time=0.8)
        self.wait(4.0)

        drive = []
        for player in lineup:
            if player.id == "pg":
                drive.append(replace(player, x=4, y=12, mass=1.42))
            elif player.id == "sg":
                drive.append(replace(player, x=-20, y=25, mass=1.35, sigma=6.2))
            elif player.team == "defense":
                drive.append(replace(player, x=player.x * 0.72, y=max(9, player.y - 4)))
            else:
                drive.append(player)
        drive_surface = _surface_from_players(drive, mode=FieldMode.NET, resolution=(40, 34), z_scale=0.78)
        drive_dots = _player_dots(drive)
        drive_badge = self.fixed_badge("DRIVE  ·  DEFENSE COMPRESSES", RED, register=False)
        self.play(
            Transform(surface, drive_surface),
            Transform(dots, drive_dots),
            Transform(badge, drive_badge),
            run_time=3.0,
            rate_func=smooth,
        )
        self.wait(5.0)

        kickout = []
        for player in drive:
            if player.id == "sg":
                kickout.append(replace(player, mass=1.9, sigma=7.0))
            elif player.id == "d1":
                kickout.append(replace(player, x=-7, y=14))
            else:
                kickout.append(player)
        kick_surface = _surface_from_players(kickout, mode=FieldMode.NET, resolution=(40, 34), z_scale=0.78)
        kick_dots = _player_dots(kickout)
        kick_badge = self.fixed_badge("KICKOUT  ·  SG OPEN 8.2 FT", BLUE, register=False)
        open_player = next(player for player in kickout if player.id == "sg")
        rings = contour_rings(open_player, BLUE, count=5)
        self.play(
            Transform(surface, kick_surface),
            Transform(dots, kick_dots),
            Transform(badge, kick_badge),
            LaggedStart(*[Create(ring) for ring in rings], lag_ratio=0.1),
            run_time=3.2,
            rate_func=smooth,
        )
        self.move_camera(phi=8 * DEGREES, theta=-90 * DEGREES, zoom=1.0, run_time=2.4)
        self.wait(7.0)
        self.play(FadeOut(card), FadeOut(badge), FadeOut(rings), FadeOut(surface), FadeOut(lines), FadeOut(dots), run_time=0.9)

    def _counterfactual(self):
        self.next_section("counterfactual-defense")
        self.set_camera_orientation(phi=57 * DEGREES, theta=-52 * DEGREES, zoom=1.08)
        shooter = Player(-17, 25, mass=1.7, sigma=6.6, team="offense", id="SG")
        helper = Player(2, 13, mass=0.95, sigma=5.0, team="offense", id="C")
        defender_late = Player(-7, 18, mass=1.18, sigma=5.3, team="defense", id="D")
        open_state = [shooter, helper, defender_late]
        surface = _surface_from_players(open_state, mode=FieldMode.NET, resolution=(44, 38), z_scale=1.0)
        lines = court_lines()
        dots = _player_dots(open_state)
        rings = contour_rings(shooter, BLUE, count=5)
        card = self.chapter_card(
            "10 · COUNTERFACTUAL",
            "What if the defender rotated sooner?",
            "Move one player, preserve everything else, and watch the opportunity disappear.",
            accent=RED,
        )
        badge = self.fixed_badge("OBSERVED  ·  SHOOTER OPEN 8.1 FT", BLUE)
        self.add(surface, lines, dots)
        self.play(FadeIn(card), FadeIn(badge), LaggedStart(*[Create(ring) for ring in rings], lag_ratio=0.1), run_time=1.8)
        self.wait(5.5)

        defender_early = replace(defender_late, x=-14.8, y=23.2, mass=1.3)
        closed_state = [shooter, helper, defender_early]
        closed_surface = _surface_from_players(closed_state, mode=FieldMode.NET, resolution=(44, 38), z_scale=1.0)
        closed_dots = _player_dots(closed_state)
        closed_badge = self.fixed_badge("COUNTERFACTUAL  ·  CONTESTED 2.6 FT", RED, register=False)
        self.play(
            FadeOut(rings),
            Transform(surface, closed_surface),
            Transform(dots, closed_dots),
            Transform(badge, closed_badge),
            run_time=3.5,
            rate_func=smooth,
        )
        self.wait(7.0)

        restored_badge = self.fixed_badge("OBSERVED  ·  ADVANTAGE RESTORED", BLUE, register=False)
        restored_rings = contour_rings(shooter, BLUE, count=5)
        self.play(
            Transform(surface, _surface_from_players(open_state, mode=FieldMode.NET, resolution=(44, 38), z_scale=1.0)),
            Transform(dots, _player_dots(open_state)),
            Transform(badge, restored_badge),
            LaggedStart(*[Create(ring) for ring in restored_rings], lag_ratio=0.1),
            run_time=3.5,
            rate_func=smooth,
        )
        self.wait(5.0)
        self.play(
            FadeOut(card),
            FadeOut(badge),
            FadeOut(restored_rings),
            FadeOut(surface),
            FadeOut(lines),
            FadeOut(dots),
            run_time=0.9,
        )

    def _coda(self):
        self.next_section("coda")
        first = Text(
            "The box score records what happened.",
            font="Segoe UI",
            font_size=38,
            color=MUTED,
        )
        second = Text(
            "Court Gravity shows why space opened.",
            font="Segoe UI",
            font_size=44,
            weight="BOLD",
            color=WHITE_SOFT,
        )
        rule = Line(LEFT * 3.4, RIGHT * 3.4, color=BLUE, stroke_width=2)
        disclaimer = Text(
            "Pedagogical model · not the proprietary NBA Gravity metric",
            font="Segoe UI",
            font_size=16,
            color=GREY_B,
        )
        group = VGroup(first, second, rule, disclaimer).arrange(DOWN, buff=0.22)
        self.add_fixed_in_frame_mobjects(group)
        self.play(FadeIn(first, shift=UP * 0.1), run_time=0.8)
        self.play(Write(second), Create(rule), run_time=1.6)
        self.play(FadeIn(disclaimer), run_time=0.5)
        self.wait(8.0)
        self.play(FadeOut(group), run_time=0.9)
