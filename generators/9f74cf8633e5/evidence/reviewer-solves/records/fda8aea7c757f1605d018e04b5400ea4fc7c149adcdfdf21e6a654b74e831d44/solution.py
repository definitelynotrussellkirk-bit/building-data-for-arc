"""Visible-example solution for task 9f74cf8633e5."""


def solve(grid):
    """Fill a blank center when its four diagonal neighbors share a nonzero color."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if grid else 0
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            diagonals = (
                grid[row - 1][col - 1],
                grid[row - 1][col + 1],
                grid[row + 1][col - 1],
                grid[row + 1][col + 1],
            )
            if grid[row][col] == 0 and diagonals[0] != 0 and len(set(diagonals)) == 1:
                out[row][col] = diagonals[0]
    return out
