"""Visible-example solution for task 6c93e8516229."""
from __future__ import annotations

from collections.abc import Sequence

Grid = list[list[int]]
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _green_components(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in _DIRECTIONS:
                    neighbor = (r + dr, c + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 3
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(cells)
    return components


def _component_color(cells: Sequence[tuple[int, int]]) -> int:
    points = set(cells)
    has_degree_three = False
    corner_count = 0

    for row, col in points:
        offsets = [
            (dr, dc)
            for dr, dc in _DIRECTIONS
            if (row + dr, col + dc) in points
        ]
        if len(offsets) == 3:
            has_degree_three = True
        elif len(offsets) == 2:
            (dr1, dc1), (dr2, dc2) = offsets
            # A path cell is a turn exactly when the two neighbors are not
            # opposite along the same row or column.
            if not (dr1 == -dr2 and dc1 == -dc2):
                corner_count += 1

    if has_degree_three:
        return 2
    if corner_count == 2:
        return 6
    return 1


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Recolor each green component according to its local topology."""
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    result = [list(row) for row in grid]
    for component in _green_components(grid):
        color = _component_color(component)
        for row, col in component:
            result[row][col] = color
    return result
