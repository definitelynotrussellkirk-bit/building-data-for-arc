"""Infer blank centers from same-colored corners of 3 by 3 windows."""


def solve(grid):
    result = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            color = grid[row - 1][col - 1]
            if color != 0 and (
                grid[row - 1][col + 1] == color
                and grid[row + 1][col - 1] == color
                and grid[row + 1][col + 1] == color
            ):
                result[row][col] = color
    return result
