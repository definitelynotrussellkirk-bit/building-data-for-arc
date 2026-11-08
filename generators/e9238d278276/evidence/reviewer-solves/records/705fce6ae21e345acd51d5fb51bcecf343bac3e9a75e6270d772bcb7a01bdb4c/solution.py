"""Visible-only solution for the blind ARC episode."""


def solve(grid):
    """Pack each column's nonzero cells at the top, preserving their order."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    result = [[0 for _ in range(width)] for _ in range(height)]

    for col in range(width):
        packed = [grid[row][col] for row in range(height) if grid[row][col] != 0]
        for row, value in enumerate(packed):
            result[row][col] = value

    return result
