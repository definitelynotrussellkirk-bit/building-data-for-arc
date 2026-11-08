"""Visible-example solution for the reviewer episode."""
from __future__ import annotations


def _solid_non_marker(values: list[int]) -> int | None:
    if values and len(set(values)) == 1 and values[0] not in (0, 1):
        return values[0]
    return None


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Project each color-1 marker one cell toward its matching colored border."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]

    top = _solid_non_marker(grid[0])
    bottom = _solid_non_marker(grid[-1])
    left = _solid_non_marker([row[0] for row in grid])
    right = _solid_non_marker([row[-1] for row in grid])

    horizontal = top is not None and bottom is not None
    vertical = left is not None and right is not None
    if horizontal == vertical:
        return result

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1:
                continue
            if horizontal:
                first = 2 * row < height
                dest_row = row - 1 if first else row + 1
                result[dest_row][col] = top if first else bottom
            else:
                first = 2 * col < width
                dest_col = col - 1 if first else col + 1
                result[row][dest_col] = left if first else right

    return result
