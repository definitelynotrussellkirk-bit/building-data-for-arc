"""Visible-example solution for the post-repair ARC episode."""
from __future__ import annotations


def solve(grid):
    """Recolor the source line to 3 and rotate its offsets clockwise in color 2."""
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError("grid must be a nonempty rectangle")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    pivots = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 5
    ]
    if len(pivots) != 1:
        raise ValueError("expected exactly one color-5 pivot")

    height = len(grid)
    pivot_row, pivot_column = pivots[0]
    output = [[0 for _ in range(width)] for _ in range(height)]
    output[pivot_row][pivot_column] = 5

    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            if value != 2:
                continue
            output[row][column] = 3
            delta_row = row - pivot_row
            delta_column = column - pivot_column
            rotated_row = pivot_row + delta_column
            rotated_column = pivot_column - delta_row
            if not (0 <= rotated_row < height and 0 <= rotated_column < width):
                raise ValueError("clockwise-rotated line leaves the grid")
            output[rotated_row][rotated_column] = 2
    return output
