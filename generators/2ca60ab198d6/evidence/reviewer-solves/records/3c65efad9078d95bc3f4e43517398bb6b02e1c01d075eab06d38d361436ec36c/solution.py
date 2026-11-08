"""Visible-example-only solution for the blind ARC episode."""


def solve(grid):
    """Keep rows whose first cell is 7, then remove that selector cell."""
    return [row[1:] for row in grid if row and row[0] == 7]
