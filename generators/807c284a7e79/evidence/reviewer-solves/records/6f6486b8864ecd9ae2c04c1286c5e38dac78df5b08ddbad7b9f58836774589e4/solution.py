"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations

from collections import deque
from copy import deepcopy


def solve(grid):
    """Flood from the unique 2 through non-8 cells and color distance parity."""
    height = len(grid)
    width = len(grid[0])
    seeds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(seeds) != 1:
        raise ValueError(f"expected one color-2 seed, found {len(seeds)}")

    start = seeds[0]
    distance = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            point = (nr, nc)
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 8
                and point not in distance
            ):
                distance[point] = distance[(r, c)] + 1
                queue.append(point)

    output = deepcopy(grid)
    for (r, c), d in distance.items():
        output[r][c] = 3 if d % 2 == 0 else 4
    return output
