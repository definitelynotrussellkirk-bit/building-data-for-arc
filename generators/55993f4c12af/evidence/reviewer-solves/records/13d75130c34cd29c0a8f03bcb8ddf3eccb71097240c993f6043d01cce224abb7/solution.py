"""Visible-example solution for review task 55993f4c12af."""


def solve(grid):
    half = len(grid) // 2
    width = len(grid[0])
    return [
        [4 if grid[row][col] != 0 or grid[row + half][col] != 0 else 0
         for col in range(width)]
        for row in range(half)
    ]
