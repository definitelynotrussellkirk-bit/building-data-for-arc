"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations

from collections.abc import Sequence


_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid: Sequence[Sequence[int]], color: int):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS4:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        found.append(component)
    return found


def solve(grid):
    """Recolor each blue object that encloses a complete maroon region."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    out = [list(row) for row in grid]
    blue_objects = _components(grid, 1)
    maroon_regions = _components(grid, 9)

    for obj in blue_objects:
        r1 = min(r for r, _ in obj)
        r2 = max(r for r, _ in obj)
        c1 = min(c for _, c in obj)
        c2 = max(c for _, c in obj)
        encloses_region = any(
            region
            and all(r1 < r < r2 and c1 < c < c2 for r, c in region)
            for region in maroon_regions
        )
        if encloses_region:
            for r, c in obj:
                out[r][c] = 8
    return out
