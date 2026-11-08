"""Visible-example solution for reviewer puzzle b0e266482663."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Cast edge-marked rays until blockers; color crossings cyan."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("solve expects a non-empty rectangular grid")

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    row_shooters = {row for row in range(1, height) if grid[row][0] == 2}
    col_shooters = {col for col in range(1, width) if grid[0][col] == 3}

    for row in range(1, height):
        horizontal_open = row in row_shooters
        for col in range(1, width):
            if grid[row][col] == 9:
                horizontal_open = False
                continue

            vertical_open = col in col_shooters and all(
                grid[above][col] != 9 for above in range(1, row + 1)
            )
            if horizontal_open and vertical_open:
                output[row][col] = 8
            elif horizontal_open:
                output[row][col] = 2
            elif vertical_open:
                output[row][col] = 3

    return output
