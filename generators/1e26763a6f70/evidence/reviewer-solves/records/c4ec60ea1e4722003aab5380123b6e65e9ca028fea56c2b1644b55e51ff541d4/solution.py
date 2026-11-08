from __future__ import annotations

from collections import defaultdict


def solve(grid):
    """Insert each repeated color at the midpoint of its aligned endpoints."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 and abs(c2 - c1) % 2 == 0:
            mr, mc = r1, (c1 + c2) // 2
        elif c1 == c2 and abs(r2 - r1) % 2 == 0:
            mr, mc = (r1 + r2) // 2, c1
        else:
            continue
        if out[mr][mc] == 0:
            out[mr][mc] = color
    return out
