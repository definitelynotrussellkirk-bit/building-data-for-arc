"""Visible-example solution for efdd2b265cc8."""


def solve(grid):
    """Reflect a rectangular grid across its main diagonal."""
    return [list(row) for row in zip(*grid)]
