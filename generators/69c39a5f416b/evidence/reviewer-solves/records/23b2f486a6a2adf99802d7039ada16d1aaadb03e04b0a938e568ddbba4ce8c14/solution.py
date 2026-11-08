from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Apply the aligned two-row color key once, then remove the key rows."""
    if len(grid) < 2:
        return []
    width = len(grid[0])
    mapping = {
        grid[0][column]: grid[1][column]
        for column in range(width)
        if grid[0][column] != 0
    }
    return [
        [mapping.get(value, value) for value in row]
        for row in grid[2:]
    ]
