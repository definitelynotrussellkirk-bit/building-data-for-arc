"""Visible-example solution for Dock the Shape to the Frame."""
from __future__ import annotations

from copy import deepcopy


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def solve(grid):
    out = deepcopy(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    red = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    cyan = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    if not red or not cyan:
        return out

    rr1, rc1, rr2, rc2 = _bbox(red)
    fr1, fc1, fr2, fc2 = _bbox(cyan)
    if rc2 < fc1:
        dr, dc = 0, 1
    elif rc1 > fc2:
        dr, dc = 0, -1
    elif rr2 < fr1:
        dr, dc = 1, 0
    else:
        dr, dc = -1, 0

    blockers = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2)
    }
    moved = set(red)
    while True:
        nxt = {(r + dr, c + dc) for r, c in moved}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in nxt):
            break
        if nxt & blockers:
            break
        moved = nxt

    for r, c in red:
        out[r][c] = 0
    for r, c in moved:
        out[r][c] = 2
    return out
