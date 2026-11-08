from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Collect every nonzero cell and return the values in ascending order."""
    values = sorted(value for row in grid for value in row if value != 0)
    return [values]
