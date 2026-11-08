"""Visible-example solution for the prepared ARC episode."""
from __future__ import annotations

from copy import deepcopy


def _blue_components(grid):
    """Return 4-connected components of blue (1) cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for column in range(width):
            if grid[row][column] != 1 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            component = []
            while stack:
                current_row, current_column = stack.pop()
                component.append((current_row, current_column))
                for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_column = current_column + delta_column
                    if (
                        0 <= next_row < height
                        and 0 <= next_column < width
                        and grid[next_row][next_column] == 1
                        and (next_row, next_column) not in seen
                    ):
                        seen.add((next_row, next_column))
                        stack.append((next_row, next_column))
            components.append(component)
    return components


def solve(grid):
    """Recolor the uniquely largest blue component orange (7)."""
    result = deepcopy(grid)
    components = _blue_components(grid)
    if not components:
        return result

    largest = max(components, key=len)
    for row, column in largest:
        result[row][column] = 7
    return result
