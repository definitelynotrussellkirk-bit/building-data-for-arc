"""Visible-example solution for task 2a5919c40197."""


def solve(grid):
    """Paint a uniform row gray (5); paint every mixed row black (0)."""
    return [
        [5 if len(set(row)) == 1 else 0] * len(row)
        for row in grid
    ]
