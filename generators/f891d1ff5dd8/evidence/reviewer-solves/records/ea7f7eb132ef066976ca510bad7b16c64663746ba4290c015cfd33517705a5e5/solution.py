"""Visible-example solution for the post-repair episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or any(not row for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if len(grid) < 2:
        raise ValueError("expected at least two preserved rows")

    output = [row[:] for row in grid]
    for row_index in range(2, len(output)):
        color = grid[0][(row_index - 2) % width]
        output[row_index] = [color] * width
    return output
