"""Visible-only solver for blind task 9bd5d9c04dd8."""

from __future__ import annotations

from collections import deque
from typing import Sequence

Grid = list[list[int]]


def _components(grid: Sequence[Sequence[int]], background: int) -> list[list[tuple[int, int]]]:
    """Return 4-connected non-background components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] == background:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(component)

    return components


def _crop(grid: Sequence[Sequence[int]], component: Sequence[tuple[int, int]]) -> Grid:
    min_row = min(row for row, _ in component)
    max_row = max(row for row, _ in component)
    min_col = min(col for _, col in component)
    max_col = max(col for _, col in component)
    return [list(row[min_col : max_col + 1]) for row in grid[min_row : max_row + 1]]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Extract the non-background tile with the greatest number of color-1 cells."""
    if not grid or not grid[0]:
        return []

    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    background = max(counts, key=counts.get)

    candidates = [_crop(grid, component) for component in _components(grid, background)]
    if not candidates:
        return []

    # Visible examples use complete 3x3 tiles.  Prefer those when present so that
    # incidental non-background noise cannot outrank a legitimate tile.
    tiles = [candidate for candidate in candidates if len(candidate) == 3 and len(candidate[0]) == 3]
    if tiles:
        candidates = tiles

    return max(candidates, key=lambda candidate: sum(value == 1 for row in candidate for value in row))
