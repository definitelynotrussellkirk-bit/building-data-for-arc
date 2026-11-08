"""Visible-example solution for task 3f93d8860778."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill a column interval only when it has exactly two equal nonzero marks."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    for column in range(width):
        marks = [(row, grid[row][column]) for row in range(height) if grid[row][column] != 0]
        if len(marks) != 2:
            continue
        (top, top_colour), (bottom, bottom_colour) = marks
        if top_colour != bottom_colour:
            continue
        for row in range(top, bottom + 1):
            output[row][column] = top_colour

    return output
