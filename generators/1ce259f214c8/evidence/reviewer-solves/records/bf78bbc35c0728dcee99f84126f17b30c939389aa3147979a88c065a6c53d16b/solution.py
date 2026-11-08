"""Visible-example solution for ARC task 1ce259f214c8."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    dividers = [
        column
        for column in range(width)
        if all(grid[row][column] == 5 for row in range(height))
    ]
    if len(dividers) != 1:
        raise ValueError("expected one full-height gray divider")
    divider = dividers[0]
    panel_width = divider
    if width != 2 * panel_width + 1:
        raise ValueError("divider must split equal-width panels")

    return [
        [
            8
            if (grid[row][column] != 0)
            != (grid[row][divider + 1 + column] != 0)
            else 0
            for column in range(panel_width)
        ]
        for row in range(height)
    ]
