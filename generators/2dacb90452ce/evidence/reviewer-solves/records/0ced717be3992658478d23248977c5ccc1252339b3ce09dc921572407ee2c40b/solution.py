"""Visible-example solution for final review episode 2dacb90452ce."""


def solve(grid):
    """Replace every source cell by a 2-by-2 block of the same color."""
    return [
        [value for value in row for _ in range(2)]
        for row in grid
        for _ in range(2)
    ]
