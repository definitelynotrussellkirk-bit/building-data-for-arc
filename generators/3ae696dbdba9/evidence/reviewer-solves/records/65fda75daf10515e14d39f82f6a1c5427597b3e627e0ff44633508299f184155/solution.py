"""Visible-example solution for task 3ae696dbdba9."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import List

Grid = List[List[int]]


def solve(grid: Grid) -> Grid:
    """Make each same-color 4-connected object vertically column-convex.

    Objects are handled independently, even when disconnected objects share a
    color.  For every occupied column of one object, fill zero cells between
    that object's highest and lowest cell in the column with the object color.
    """
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output = deepcopy(grid)
    seen: set[tuple[int, int]] = set()

    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            component: list[tuple[int, int]] = []

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))

            rows_by_column: dict[int, list[int]] = {}
            for r, c in component:
                rows_by_column.setdefault(c, []).append(r)

            for c, rows in rows_by_column.items():
                top, bottom = min(rows), max(rows)
                for r in range(top, bottom + 1):
                    if output[r][c] == 0:
                        output[r][c] = color

    return output
