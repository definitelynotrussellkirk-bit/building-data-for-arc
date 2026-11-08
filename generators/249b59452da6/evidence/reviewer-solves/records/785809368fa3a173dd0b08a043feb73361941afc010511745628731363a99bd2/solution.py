"""Visible-example solution for the exposed, post-repair episode."""


def solve(grid):
    result = [row[:] for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a == e == 2 and b == d == 0:
                result[r][c + 1] = 3
                result[r + 1][c] = 3
            elif b == d == 2 and a == e == 0:
                result[r][c] = 3
                result[r + 1][c + 1] = 3
    return result
