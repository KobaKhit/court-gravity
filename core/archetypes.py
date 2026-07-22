"""Role archetype presets: anchors, masses, effectiveness surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .court import CourtConfig, load_court_config
from .field import Player
from .kde import (
    lockdown_effectiveness,
    playmaker_effectiveness,
    rim_runner_effectiveness,
    sharpshooter_effectiveness,
)
from .trajectories import AgentState


Role = Literal["sharpshooter", "rim_runner", "playmaker", "lockdown", "wing"]


@dataclass
class Archetype:
    role: Role
    team: str
    anchor: tuple[float, float]
    mass: float
    sigma: float
    stats: dict


ARCHETYPES: dict[str, Archetype] = {
    "sharpshooter": Archetype(
        role="sharpshooter",
        team="offense",
        anchor=(-18.0, 22.0),
        mass=1.4,
        sigma=6.0,
        stats={"three_pt_pct": 0.43, "usage": 0.28, "rim_fg_pct": 0.55},
    ),
    "rim_runner": Archetype(
        role="rim_runner",
        team="offense",
        anchor=(0.0, 6.0),
        mass=1.1,
        sigma=4.5,
        stats={"three_pt_pct": 0.28, "usage": 0.22, "rim_fg_pct": 0.72},
    ),
    "playmaker": Archetype(
        role="playmaker",
        team="offense",
        anchor=(0.0, 26.0),
        mass=1.2,
        sigma=5.5,
        stats={"three_pt_pct": 0.37, "usage": 0.30, "rim_fg_pct": 0.58},
    ),
    "wing": Archetype(
        role="wing",
        team="offense",
        anchor=(18.0, 20.0),
        mass=0.9,
        sigma=5.0,
        stats={"three_pt_pct": 0.36, "usage": 0.18, "rim_fg_pct": 0.60},
    ),
    "lockdown": Archetype(
        role="lockdown",
        team="defense",
        anchor=(0.0, 22.0),
        mass=1.0,
        sigma=5.0,
        stats={"def_rating": 105.0, "usage": 0.0},
    ),
}


def effectiveness_for_role(role: str, court: CourtConfig | None = None) -> np.ndarray:
    court = court or load_court_config()
    if role == "sharpshooter":
        return sharpshooter_effectiveness(court)
    if role == "rim_runner":
        return rim_runner_effectiveness(court)
    if role == "playmaker":
        return playmaker_effectiveness(court)
    if role == "lockdown":
        return lockdown_effectiveness(court)
    # wing: mild corners + wing
    from .kde import hot_zone_surface

    _, _, G = hot_zone_surface([(18.0, 20.0), (16.0, 8.0)], court, sigma=4.0)
    return G


def mass_from_stats(base: float, stats: dict, *, team: str = "offense") -> float:
    """Map exposed stats onto amplitude."""
    if team == "defense":
        # Lower def_rating → taller ridge (better defense)
        dr = float(stats.get("def_rating", 110.0))
        return base * (115.0 / max(dr, 90.0))
    usage = float(stats.get("usage", 0.2))
    three = float(stats.get("three_pt_pct", 0.35))
    return base * (0.5 + usage) * (0.7 + (three - 0.33) * 2.0)


def make_player(
    role: str,
    *,
    player_id: str | None = None,
    x: float | None = None,
    y: float | None = None,
    court: CourtConfig | None = None,
    with_effectiveness: bool = True,
    stats_override: dict | None = None,
) -> Player:
    court = court or load_court_config()
    arch = ARCHETYPES[role]
    stats = {**arch.stats, **(stats_override or {})}
    ax, ay = arch.anchor
    m = mass_from_stats(arch.mass, stats, team=arch.team)
    eff = effectiveness_for_role(role, court) if with_effectiveness else None
    return Player(
        x=ax if x is None else x,
        y=ay if y is None else y,
        mass=m,
        sigma=arch.sigma,
        team=arch.team,
        id=player_id or role,
        role=role,
        effectiveness=eff,
    )


def default_lineup(court: CourtConfig | None = None, with_effectiveness: bool = True) -> list[Player]:
    """5 offense + 5 defense lineup."""
    court = court or load_court_config()
    offense_roles = ["playmaker", "sharpshooter", "wing", "rim_runner", "wing"]
    offense_ids = ["pg", "sg", "sf", "c", "pf"]
    # Second wing on left
    players: list[Player] = []
    for role, pid in zip(offense_roles, offense_ids):
        p = make_player(role, player_id=pid, court=court, with_effectiveness=with_effectiveness)
        if pid == "pf":
            p.x, p.y = -16.0, 12.0
        players.append(p)

    # Defense mirrors offense assignments
    assigns = ["pg", "sg", "sf", "c", "pf"]
    anchors = [(0, 24), (-14, 20), (14, 18), (2, 8), (-10, 12)]
    for i, (oid, (ax, ay)) in enumerate(zip(assigns, anchors)):
        d = make_player(
            "lockdown",
            player_id=f"d{i}",
            x=ax,
            y=ay,
            court=court,
            with_effectiveness=with_effectiveness,
        )
        players.append(d)
    return players


def lineup_as_agents(court: CourtConfig | None = None) -> list[AgentState]:
    court = court or load_court_config()
    players = default_lineup(court, with_effectiveness=False)
    agents: list[AgentState] = []
    offense = [p for p in players if p.team == "offense"]
    defense = [p for p in players if p.team == "defense"]
    for p in offense:
        agents.append(
            AgentState(
                id=p.id,
                role=p.role,
                team=p.team,
                x=p.x,
                y=p.y,
                anchor_x=p.x,
                anchor_y=p.y,
                mass=p.mass,
                sigma=p.sigma,
            )
        )
    for i, d in enumerate(defense):
        agents.append(
            AgentState(
                id=d.id,
                role=d.role,
                team=d.team,
                x=d.x,
                y=d.y,
                anchor_x=d.x,
                anchor_y=d.y,
                mass=d.mass,
                sigma=d.sigma,
                respect=0.55 + 0.1 * (i % 3),
                assigned_offense_id=offense[i % len(offense)].id,
            )
        )
    return agents
