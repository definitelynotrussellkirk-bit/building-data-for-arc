"""Visible-example solution bound to the final generator source."""


def solve(grid):
    """Retain guide-7 rows in order and remove column zero."""
    return [row[1:] for row in grid if row and row[0] == 7]
