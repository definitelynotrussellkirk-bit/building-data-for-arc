from __future__ import annotations

from collections import defaultdict


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the empty midpoint of each aligned same-color endpoint pair."""
    out = [list(row) for row in grid]
    cells: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                cells[color].append((r, c))

    for color, points in cells.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2 and (c1 + c2) % 2 == 0:
            mr, mc = r1, (c1 + c2) // 2
        elif c1 == c2 and (r1 + r2) % 2 == 0:
            mr, mc = (r1 + r2) // 2, c1
        else:
            continue
        if grid[mr][mc] == 0:
            out[mr][mc] = color
    return out
