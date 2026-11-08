"""Visible-example solution for the assigned ARC episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy the input on the 2x2 block diagonal and mark qualifying blank rows."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    nonblank_rows = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    last_nonblank = max(nonblank_rows, default=-1)
    output = [[0 for _ in range(2 * width)] for _ in range(2 * height)]

    for r, row in enumerate(grid):
        qualifying_blank = not any(value != 0 for value in row) and r <= last_nonblank
        if qualifying_blank:
            output[r] = [3] * (2 * width)
            output[r + height] = [3] * (2 * width)
            continue

        output[r][:width] = row[:]
        output[r + height][width:] = row[:]

    return output
