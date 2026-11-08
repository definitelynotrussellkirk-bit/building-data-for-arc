"""Visible-only solution for blind task 88b8e6aaa49d."""


def solve(grid):
    """Rotate the rectangular grid by 180 degrees."""
    return [list(reversed(row)) for row in reversed(grid)]
