"""Visible-example solution for reviewer-authored task 3a0af56db83e."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay four aligned 3-row panels in the inferred priority 0, 1, 3, 2."""
    if len(grid) != 12 or not grid or not grid[0]:
        raise ValueError("expected a nonempty 12-row grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    output = [[0 for _ in range(width)] for _ in range(3)]
    for row in range(3):
        for col in range(width):
            for panel in (0, 1, 3, 2):
                value = grid[panel * 3 + row][col]
                if value != 0:
                    output[row][col] = value
                    break
    return output
