"""Visible-example-only solution for the blind ARC episode."""
from __future__ import annotations

from collections import deque
from typing import List

Grid = List[List[int]]


def solve(grid: Grid) -> Grid:
    """Complete each colored component's bounding box as a framed checkerboard.

    Every non-background 4-connected component supplies a color and the extent of
    a rectangle.  The output draws that rectangle's border solidly and fills its
    interior with the same color on even local parity cells, leaving the opposite
    parity cells as background.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue

            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            r_min = min(r for r, _ in cells)
            r_max = max(r for r, _ in cells)
            c_min = min(c for _, c in cells)
            c_max = max(c for _, c in cells)

            for r in range(r_min, r_max + 1):
                for c in range(c_min, c_max + 1):
                    local_r = r - r_min
                    local_c = c - c_min
                    on_border = r in (r_min, r_max) or c in (c_min, c_max)
                    out[r][c] = color if on_border or (local_r + local_c) % 2 == 0 else 0

    return out
