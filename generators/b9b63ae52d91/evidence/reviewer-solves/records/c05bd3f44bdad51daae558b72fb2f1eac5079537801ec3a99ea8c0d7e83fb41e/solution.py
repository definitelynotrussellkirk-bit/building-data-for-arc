"""Visible-example solution for the post-repair reviewer episode."""


def solve(grid):
    height = len(grid)
    return [
        [
            0
            if value == 0
            else 2 if grid[height - 1 - row][col] == 8 else 5
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]
