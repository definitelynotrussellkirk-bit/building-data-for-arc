"""Visible-example solution for 9a35b20efa99."""
from __future__ import annotations


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return _rotate_cw(_rotate_cw(grid))


def _rotate_ccw(grid):
    return _rotate_cw(_rotate_180(grid))


def solve(grid):
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        raise ValueError(f"expected exactly one color-9 anchor, found {len(anchors)}")
    ar, ac = anchors[0]

    motif = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 9)]
    if not motif:
        raise ValueError("expected a nonzero motif besides the anchor")
    r0, r1 = min(r for r, _ in motif), max(r for r, _ in motif)
    c0, c1 = min(c for _, c in motif), max(c for _, c in motif)
    crop = [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]
    ch, cw = len(crop), len(crop[0])

    variants = (crop, _rotate_cw(crop), _rotate_180(crop), _rotate_ccw(crop))
    offsets = ((-ch - 1, -cw - 1), (-ch - 1, 1), (1, -cw - 1), (1, 1))
    out = [[0] * w for _ in range(h)]
    out[ar][ac] = 9
    for variant, (dr, dc) in zip(variants, offsets):
        for r, row in enumerate(variant):
            for c, value in enumerate(row):
                rr, cc = ar + dr + r, ac + dc + c
                if value and 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = value
    return out
