"""Visible-example solution for reviewer solve task 8ff1ff513757."""


def solve(grid):
    """Remove every all-zero row and preserve all other rows in order."""
    return [list(row) for row in grid if any(value != 0 for value in row)]
