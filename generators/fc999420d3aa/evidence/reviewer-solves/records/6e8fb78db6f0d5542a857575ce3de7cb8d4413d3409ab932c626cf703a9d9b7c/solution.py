"""Visible-example solution for fc999420d3aa."""
from __future__ import annotations

from copy import deepcopy


DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid):
    """Complete every same-colour plus that has exactly one missing arm."""
    out = deepcopy(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    fills = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            neighbors = [(r + dr, c + dc) for dr, dc in DIRS]
            if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in neighbors):
                continue
            same = [(rr, cc) for rr, cc in neighbors if grid[rr][cc] == color]
            empty = [(rr, cc) for rr, cc in neighbors if grid[rr][cc] == 0]
            if len(same) == 3 and len(empty) == 1:
                rr, cc = empty[0]
                fills.append((rr, cc, color))

    for r, c, color in fills:
        out[r][c] = color
    return out
