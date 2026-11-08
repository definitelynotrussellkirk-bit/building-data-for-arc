"""Visible-example solution for blind task 55cfa127936a."""


def solve(grid):
    """Keep only the topmost non-background cell in each column."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]

    for col in range(width):
        for row in range(height):
            value = grid[row][col]
            if value != 0:
                out[row][col] = value
                break

    return out
