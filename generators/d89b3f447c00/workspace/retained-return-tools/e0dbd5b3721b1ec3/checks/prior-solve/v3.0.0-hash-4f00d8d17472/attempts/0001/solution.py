"""Visible-example solution for d89b3f447c00.

For each non-background color, find every axis-aligned rectangle whose four
corners contain exactly three cells of that color in the original input, then
paint the missing corner with the same color.  All detections are made from the
original grid so newly completed corners do not trigger a second wave.
"""

from __future__ import annotations

from itertools import combinations


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0]) if isinstance(grid[0], list) else 0
    if width == 0:
        raise ValueError("grid rows must be non-empty lists")
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int for cell in row):
            raise TypeError("grid cells must be integers")
    return len(grid), width


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete every same-color three-corner axis-aligned rectangle."""
    height, width = _validate_grid(grid)
    source = [row[:] for row in grid]
    result = [row[:] for row in grid]

    colors = sorted({cell for row in source for cell in row if cell != 0})
    for color in colors:
        rows = sorted({r for r in range(height) for c in range(width) if source[r][c] == color})
        columns = sorted({c for r in range(height) for c in range(width) if source[r][c] == color})
        for top, bottom in combinations(rows, 2):
            for left, right in combinations(columns, 2):
                corners = (
                    (top, left),
                    (top, right),
                    (bottom, left),
                    (bottom, right),
                )
                matching = [source[r][c] == color for r, c in corners]
                if sum(matching) == 3:
                    missing = matching.index(False)
                    r, c = corners[missing]
                    result[r][c] = color

    return result
