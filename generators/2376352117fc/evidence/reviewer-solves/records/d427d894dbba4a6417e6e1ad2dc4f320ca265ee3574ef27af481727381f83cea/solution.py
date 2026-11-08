"""Solve the visible marker-displacement task without external dependencies."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("Expected a nonempty grid")
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        raise ValueError("Expected nonempty rows")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("Grid cells must be integer colors 0 through 9")
    markers = {color: [(r, c) for r, row in enumerate(grid)
                       for c, value in enumerate(row) if value == color]
               for color in (1, 2)}
    if any(len(cells) != 1 for cells in markers.values()):
        raise ValueError("Expected one blue and one red marker")
    blue, red = markers[1][0], markers[2][0]
    dr, dc = red[0] - blue[0], red[1] - blue[1]
    output = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            rr, cc = r + dr, c + dc
            if value == 3 and 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = 8
    return output
