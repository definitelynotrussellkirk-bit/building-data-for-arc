"""Visible-example solution for task 2c83e8cd1c07."""
from __future__ import annotations

from copy import deepcopy
from collections import defaultdict


def solve(grid):
    """Fill clear 45-degree spans between two cells of the same color.

    A pair is filled only when every interior cell on that diagonal is zero in
    the original input.  All eligibility decisions are therefore simultaneous.
    """
    out = deepcopy(grid)
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        row_delta = r2 - r1
        col_delta = c2 - c1
        if row_delta == 0 or abs(row_delta) != abs(col_delta):
            continue
        dr = 1 if row_delta > 0 else -1
        dc = 1 if col_delta > 0 else -1
        distance = abs(row_delta)
        path = [(r1 + step * dr, c1 + step * dc) for step in range(distance + 1)]
        if all(grid[r][c] == 0 for r, c in path[1:-1]):
            for r, c in path:
                out[r][c] = color
    return out
