"""Visible-example solution for the prepared reviewer episode."""


def solve(grid):
    """Flood a row with its first value, or clear it when that value is zero."""
    return [[row[0]] * len(row) if row and row[0] != 0 else [0] * len(row) for row in grid]
