"""Pure-Python value / Perlin-like noise (no native deps)."""

from __future__ import annotations

import math


def _fade(t: float) -> float:
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: float, b: float, t: float) -> float:
    return a + t * (b - a)


def _grad(hash_: int, x: float, y: float) -> float:
    h = hash_ & 7
    u = x if h < 4 else y
    v = y if h < 4 else x
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)


# Fixed permutation table
_PERM = list(range(256))
# Deterministic shuffle
_a, _c, _m = 1103515245, 12345, 2**31
_seed = 42
for i in range(255, 0, -1):
    _seed = (_a * _seed + _c) % _m
    j = _seed % (i + 1)
    _PERM[i], _PERM[j] = _PERM[j], _PERM[i]
_PERM = _PERM + _PERM


def pnoise2(x: float, y: float, repeatx: int = 1024, repeaty: int = 1024, base: int = 0) -> float:
    """2D Perlin-like noise in roughly [-1, 1]. Compatible call shape with `noise.pnoise2`."""
    _ = (repeatx, repeaty)
    x += base * 0.37
    y += base * 0.91
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    xf = x - math.floor(x)
    yf = y - math.floor(y)
    u = _fade(xf)
    v = _fade(yf)
    aa = _PERM[_PERM[xi] + yi]
    ab = _PERM[_PERM[xi] + yi + 1]
    ba = _PERM[_PERM[xi + 1] + yi]
    bb = _PERM[_PERM[xi + 1] + yi + 1]
    x1 = _lerp(_grad(aa, xf, yf), _grad(ba, xf - 1, yf), u)
    x2 = _lerp(_grad(ab, xf, yf - 1), _grad(bb, xf - 1, yf - 1), u)
    return _lerp(x1, x2, v)
