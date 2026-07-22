#!/usr/bin/env python3
"""Generate synthetic trajectory JSON + field exports for the web app."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.archetypes import default_lineup, lineup_as_agents, make_player
from core.court import load_court_config
from core.export import export_field, export_trajectories_json, players_to_shader_uniforms
from core.field import Player
from core.trajectories import TrajectoryConfig, simulate


def main() -> None:
    court = load_court_config()
    out = ROOT / "data" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)

    # Static archetype fields
    for role in ("sharpshooter", "rim_runner", "playmaker", "lockdown"):
        p = make_player(role, court=court, with_effectiveness=True)
        export_field(out / "fields", [p], court=court, stem=role)

    lineup = default_lineup(court, with_effectiveness=True)
    export_field(out / "fields", lineup, court=court, stem="full_lineup")

    # Trajectories
    agents = lineup_as_agents(court)
    data = simulate(agents, court=court, cfg=TrajectoryConfig(duration=10.0, seed=3))
    export_trajectories_json(out / "trajectories.json", data)

    # Shader snapshot at t=0
    snap = [
        Player(
            x=p["traj"][0][1],
            y=p["traj"][0][2],
            mass=p["stats"]["base_mass"],
            sigma=p["stats"]["sigma"],
            team=p["team"],
            id=p["id"],
            role=p["role"],
        )
        for p in data["players"]
    ]
    uniforms = players_to_shader_uniforms(snap)
    (out / "shader_uniforms.json").write_text(json.dumps(uniforms, indent=2), encoding="utf-8")

    # Copy configs into data for web
    for name in ("court_config.json", "palette.json"):
        src = ROOT / "configs" / name
        (out / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Generated synthetic data in {out}")


if __name__ == "__main__":
    main()
