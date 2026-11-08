from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


def solve(grid):
    """Bridge a colour only when it occurs exactly twice on one row/column."""
    output = deepcopy(grid)
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for color, points in positions.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                output[r1][c] = color
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                output[r][c1] = color
    return output
