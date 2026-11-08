from __future__ import annotations

from collections import deque
from typing import List

Grid = List[List[int]]


def solve(grid: Grid) -> Grid:
    """Propagate each connected network's marker into its enclosed cells."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue

            component: list[tuple[int, int]] = []
            marker_color: int | None = None
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                value = grid[row][col]
                if value not in (0, 1):
                    marker_color = value

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            if marker_color is None:
                continue

            for row, col in component:
                if row == 0 or row == height - 1 or col == 0 or col == width - 1:
                    continue
                if all(
                    grid[row + dr][col + dc] != 0
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                    if (dr, dc) != (0, 0)
                ):
                    output[row][col] = marker_color

    return output
