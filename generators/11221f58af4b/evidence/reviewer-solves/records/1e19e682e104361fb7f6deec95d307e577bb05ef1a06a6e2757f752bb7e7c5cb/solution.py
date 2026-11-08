"""Blind solution for task 11221f58af4b.

The corner markers select the paint color (the repeated non-zero corner
color). Every background region completely enclosed by color 3 is painted.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import List

Grid = List[List[int]]


def solve(grid: Grid) -> Grid:
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]

    corner_values = (grid[0][0], grid[0][w - 1], grid[h - 1][0], grid[h - 1][w - 1])
    candidates = [value for value in corner_values if value not in (0, 3)]
    if not candidates:
        return out
    fill_color = Counter(candidates).most_common(1)[0][0]

    # Mark every zero reachable from the exterior. Any unmarked zero is a hole
    # enclosed by the color-3 frames and should receive the selected color.
    exterior: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    def seed(r: int, c: int) -> None:
        if grid[r][c] == 0 and (r, c) not in exterior:
            exterior.add((r, c))
            queue.append((r, c))

    for c in range(w):
        seed(0, c)
        seed(h - 1, c)
    for r in range(h):
        seed(r, 0)
        seed(r, w - 1)

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0 and (nr, nc) not in exterior:
                exterior.add((nr, nc))
                queue.append((nr, nc))

    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 and (r, c) not in exterior:
                out[r][c] = fill_color

    return out
