"""Visible-example solution for b3bfd59c2c43."""
from __future__ import annotations

from collections import deque

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid):
    """Recolor the cardinal boundary of each nonzero connected component to 8."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}

    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)

        for r, c in component:
            if any(
                not (0 <= r + dr < h and 0 <= c + dc < w)
                or (r + dr, c + dc) not in component
                for dr, dc in CARDINAL
            ):
                out[r][c] = 8
    return out
