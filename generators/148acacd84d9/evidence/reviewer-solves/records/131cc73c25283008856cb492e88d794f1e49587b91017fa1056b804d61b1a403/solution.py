"""Visible-example solution: turn the complete canvas clockwise by 90 degrees."""


def solve(grid):
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")
    return [[grid[height - 1 - column][row] for column in range(height)]
            for row in range(width)]
