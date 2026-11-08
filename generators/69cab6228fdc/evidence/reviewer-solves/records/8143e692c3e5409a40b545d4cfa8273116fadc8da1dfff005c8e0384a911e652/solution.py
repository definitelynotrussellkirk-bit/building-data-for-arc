from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the two-row legend plus separator, then apply its color mapping."""
    mapping = {
        source: target
        for source, target in zip(grid[0], grid[1])
        if source != 0 and target != 0
    }
    return [
        [mapping.get(value, value) for value in row]
        for row in grid[3:]
    ]
