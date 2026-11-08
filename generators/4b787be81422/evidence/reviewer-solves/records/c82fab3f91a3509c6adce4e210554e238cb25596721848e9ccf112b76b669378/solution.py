"""Visible-example solution for task 4b787be81422."""


def solve(grid):
    """Classify reflection symmetry about the vertical axis."""
    symmetric = all(list(row) == list(reversed(row)) for row in grid)
    return [[1 if symmetric else 7]]
