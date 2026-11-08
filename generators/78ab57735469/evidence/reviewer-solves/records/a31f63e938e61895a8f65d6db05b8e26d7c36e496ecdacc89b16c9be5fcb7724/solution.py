"""Visible-example solution for 78ab57735469."""


def solve(grid):
    n = len(grid)
    return [
        [
            grid[
                n - 1 - (row % n) if (row // n) % 2 == 0 else row % n
            ][
                n - 1 - (col % n) if (col // n) % 2 == 0 else col % n
            ]
            for col in range(3 * n)
        ]
        for row in range(3 * n)
    ]
