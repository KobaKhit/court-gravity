"""Offensive/defensive effectiveness surfaces via KDE / hot-zone Gaussians."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.stats import gaussian_kde

from .court import CourtConfig, load_court_config, sample_three_point_ring


def kde_surface(
    points: np.ndarray,
    court: CourtConfig | None = None,
    *,
    weights: np.ndarray | None = None,
    bandwidth: str | float = "silverman",
    nx: int | None = None,
    ny: int | None = None,
    normalize: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a KDE effectiveness surface from shot/location samples.

    points: (N, 2) array of (x, y) in court feet.
    Returns XX, YY, G with G ≥ 0, optionally max-normalized to 1.
    """
    court = court or load_court_config()
    XX, YY = court.meshgrid(nx, ny)
    if len(points) < 2:
        G = np.zeros_like(XX)
        return XX, YY, G

    pts = np.asarray(points, dtype=np.float64).T  # shape (2, N)
    kde = gaussian_kde(pts, bw_method=bandwidth, weights=weights)
    positions = np.vstack([XX.ravel(), YY.ravel()])
    G = kde(positions).reshape(XX.shape)
    if normalize and G.max() > 0:
        G = G / G.max()
    return XX, YY, G


def hot_zone_surface(
    centers: Sequence[tuple[float, float]],
    court: CourtConfig | None = None,
    *,
    sigma: float = 3.0,
    amplitudes: Sequence[float] | None = None,
    nx: int | None = None,
    ny: int | None = None,
    normalize: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sum of isotropic Gaussians at hot-zone centers (fast, no scipy KDE)."""
    court = court or load_court_config()
    XX, YY = court.meshgrid(nx, ny)
    G = np.zeros_like(XX)
    amps = amplitudes or [1.0] * len(centers)
    for (cx, cy), a in zip(centers, amps):
        G += a * np.exp(-0.5 * ((XX - cx) ** 2 + (YY - cy) ** 2) / (sigma**2))
    if normalize and G.max() > 0:
        G = G / G.max()
    return XX, YY, G


def sharpshooter_effectiveness(court: CourtConfig | None = None, **kwargs) -> np.ndarray:
    """Ring of hot zones along the 3-point arc."""
    court = court or load_court_config()
    ring = sample_three_point_ring(court, n=16)
    # Add corner spots
    half_w = court.width / 2.0
    corners = np.array([[-half_w + 3, 0.0], [half_w - 3, 0.0]])
    # Corner threes are near baseline along sideline — use y≈0..5 for corner
    corners = np.array([[-22.0, 3.0], [22.0, 3.0]])
    pts = np.vstack([ring, corners])
    # Jitter for KDE
    rng = np.random.default_rng(42)
    samples = pts[rng.integers(0, len(pts), size=200)] + rng.normal(0, 0.8, size=(200, 2))
    _, _, G = kde_surface(samples, court, **kwargs)
    return G


def rim_runner_effectiveness(court: CourtConfig | None = None, **kwargs) -> np.ndarray:
    """Deep crater at the rim."""
    court = court or load_court_config()
    rng = np.random.default_rng(7)
    samples = rng.normal(loc=[0.0, 2.0], scale=[2.5, 2.5], size=(250, 2))
    _, _, G = kde_surface(samples, court, **kwargs)
    return G


def playmaker_effectiveness(court: CourtConfig | None = None, **kwargs) -> np.ndarray:
    """Moderate well at top of the key / free-throw line."""
    court = court or load_court_config()
    rng = np.random.default_rng(11)
    samples = rng.normal(loc=[0.0, 19.0], scale=[4.0, 3.0], size=(200, 2))
    _, _, G = kde_surface(samples, court, **kwargs)
    return G


def lockdown_effectiveness(court: CourtConfig | None = None, **kwargs) -> np.ndarray:
    """
    Defensive suppression surface — elevated where the defender is effective.
    For a tracking defender this is often near-uniform; use a broad blob.
    """
    court = court or load_court_config()
    _, _, G = hot_zone_surface([(0.0, 20.0)], court, sigma=18.0, **kwargs)
    return G


def linear_bin_blur_kde(
    points: np.ndarray,
    court: CourtConfig | None = None,
    *,
    sigma_bins: float = 2.0,
    nx: int | None = None,
    ny: int | None = None,
    normalize: bool = True,
) -> np.ndarray:
    """Fast approximate KDE via linear binning + Gaussian blur (separable)."""
    from scipy.ndimage import gaussian_filter

    court = court or load_court_config()
    nx = nx or court.nx
    ny = ny or court.ny
    x0, x1 = court.x_extent
    y0, y1 = court.y_extent
    hist, _, _ = np.histogram2d(
        points[:, 1],
        points[:, 0],
        bins=[ny, nx],
        range=[[y0, y1], [x0, x1]],
    )
    G = gaussian_filter(hist.astype(np.float64), sigma=sigma_bins)
    if normalize and G.max() > 0:
        G = G / G.max()
    return G
