"""Visible-example-only solution for the assigned blind ARC task."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Remove the direction marker (9) and move all other colors one cell toward it."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one marker color 9, found {len(markers)}")

    marker_row, marker_col = markers[0]
    if marker_row == 0:
        delta_row, delta_col = -1, 0
    elif marker_row == height - 1:
        delta_row, delta_col = 1, 0
    elif marker_col == 0:
        delta_row, delta_col = 0, -1
    elif marker_col == width - 1:
        delta_row, delta_col = 0, 1
    else:
        raise ValueError("marker 9 must lie on a grid border")

    result = [[0 for _ in range(width)] for _ in range(height)]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 9):
                continue
            target_row = row + delta_row
            target_col = col + delta_col
            if not (0 <= target_row < height and 0 <= target_col < width):
                raise ValueError("a colored cell would move outside the grid")
            result[target_row][target_col] = value
    return result
