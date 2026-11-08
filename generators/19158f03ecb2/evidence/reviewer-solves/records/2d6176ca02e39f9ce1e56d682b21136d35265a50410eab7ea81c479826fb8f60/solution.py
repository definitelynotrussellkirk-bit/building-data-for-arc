from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Append a horizontal reflection of the input to its right side."""
    return [list(row) + list(reversed(row)) for row in grid]
