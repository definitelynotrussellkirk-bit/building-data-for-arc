from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace every input cell with a 2x2 block of the same color."""
    return [
        [value for value in row for _ in range(2)]
        for row in grid
        for _ in range(2)
    ]
