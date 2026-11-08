"""Placement utilities — finding positions on a grid."""
from __future__ import annotations

import random
from typing import Sequence

from .grid import Grid


Cell = tuple[int, int]


def random_position(
    rng: random.Random, h: int, w: int, *, margin: int = 0,
) -> tuple[int, int]:
    """A random (r, c) at least `margin` cells from every edge."""
    if margin < 0:
        raise ValueError("random_position: margin must be >= 0")
    if 2 * margin >= h or 2 * margin >= w:
        raise ValueError(
            f"random_position: margin {margin} too large for grid {h}x{w}")
    return (rng.randint(margin, h - 1 - margin),
            rng.randint(margin, w - 1 - margin))


def random_free_cell(
    g: Grid, rng: random.Random, *, bg: int = 0, max_tries: int = 50,
) -> tuple[int, int] | None:
    """Return a random (r, c) where g[r][c] == bg, or None after max_tries."""
    h = len(g)
    w = len(g[0]) if g else 0
    if h == 0 or w == 0:
        return None
    for _ in range(max_tries):
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] == bg:
            return (r, c)
    return None


def place_no_overlap(
    rng: random.Random,
    g: Grid,
    cells: Sequence[Cell],
    color: int,
    *,
    bg: int = 0,
    margin: int = 0,
    padding: int = 0,
    max_tries: int = 100,
) -> tuple[int, int] | None:
    """Try to place a normalized shape (origin (0,0)) onto g, painting it
    in `color` at a random offset where every shape-cell lands on `bg`
    (no overlap with existing non-bg content) and the bbox stays inside
    the grid with `margin` padding.

    `padding` (≥0) requires every cell within Chebyshev distance ≤ padding
    of any shape cell to also be `bg`, preventing the new shape from
    touching any existing non-bg content (useful when downstream rules
    use 4- or 8-connectivity to find separate objects).

    Returns the (rr, rc) offset chosen, or None if `max_tries` exhausted.
    Mutates `g` only on success."""
    if not cells:
        return None
    h = len(g)
    w = len(g[0]) if g else 0
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    min_r, min_c = min(rs), min(cs)
    sh = max(rs) - min_r + 1
    sw = max(cs) - min_c + 1
    max_rr = h - sh - margin
    max_rc = w - sw - margin
    if max_rr < margin or max_rc < margin:
        return None
    cell_set = {(dr - min_r, dc - min_c) for dr, dc in cells}
    if padding > 0:
        check_set = set()
        for sr, sc in cell_set:
            for pr in range(-padding, padding + 1):
                for pc in range(-padding, padding + 1):
                    check_set.add((sr + pr, sc + pc))
    else:
        check_set = cell_set
    for _ in range(max_tries):
        rr = rng.randint(margin, max_rr)
        rc = rng.randint(margin, max_rc)
        clear = True
        for sr, sc in check_set:
            r = rr + sr
            c = rc + sc
            if r < 0 or r >= h or c < 0 or c >= w:
                continue
            if g[r][c] != bg:
                clear = False
                break
        if clear:
            for sr, sc in cell_set:
                g[rr + sr][rc + sc] = color
            return (rr, rc)
    return None
