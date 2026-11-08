"""Visible-example solution for task 1a8932958b14."""
from __future__ import annotations


def solve(grid):
    """Move every non-background, non-marker payload cell by red→green."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    height = len(grid)
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    red = []
    green = []
    payload = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 2:
                red.append((row, col))
            elif value == 3:
                green.append((row, col))
            elif value != 0:
                payload.append((row, col, value))

    if len(red) != 1 or len(green) != 1:
        raise ValueError("expected exactly one red source and one green destination")
    dr = green[0][0] - red[0][0]
    dc = green[0][1] - red[0][1]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col, value in payload:
        new_row = row + dr
        new_col = col + dc
        if not (0 <= new_row < height and 0 <= new_col < width):
            raise ValueError("marker vector moves payload out of bounds")
        output[new_row][new_col] = value
    return output
