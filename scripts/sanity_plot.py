#!/usr/bin/env python3
"""Sanity plot: one static Gaussian well over a half-court."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.court import load_court_config
from core.export import export_field
from core.field import Player, evaluate_grid


def main() -> None:
    court = load_court_config()
    players = [Player(x=0.0, y=20.0, mass=1.5, sigma=5.0, team="offense", id="curry")]
    XX, YY, Z = evaluate_grid(players, court)

    out = ROOT / "data" / "sanity"
    meta = export_field(out, players, court=court, stem="single_well")

    fig, ax = plt.subplots(figsize=(7, 6.5), facecolor="#111111")
    ax.set_facecolor("#111111")
    vmax = max(abs(Z.min()), abs(Z.max()))
    im = ax.pcolormesh(XX, YY, Z, shading="auto", cmap="RdYlBu_r", vmin=-vmax, vmax=vmax)
    ax.plot(0, 20, "o", color="#58C4DD", markersize=10, label="player")
    # Simple court outline
    x0, x1 = court.x_extent
    y0, y1 = court.y_extent
    ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color="white", lw=1, alpha=0.5)
    ax.set_aspect("equal")
    ax.set_title("Single offensive gravity well", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#888888")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")
    fig.savefig(out / "sanity_plot.png", dpi=150, facecolor=fig.get_facecolor())
    print(f"Wrote {out} z=[{meta['z_min']:.3f}, {meta['z_max']:.3f}]")
    # Analytic peak check: at player center, |z| should be ~ mass
    z_center = float(
        Z[
            np.abs(YY[:, 0] - 20.0).argmin(),
            np.abs(XX[0, :] - 0.0).argmin(),
        ]
    )
    assert z_center < -1.0, f"expected deep well, got {z_center}"
    print(f"Center height {z_center:.3f} OK")


if __name__ == "__main__":
    main()
