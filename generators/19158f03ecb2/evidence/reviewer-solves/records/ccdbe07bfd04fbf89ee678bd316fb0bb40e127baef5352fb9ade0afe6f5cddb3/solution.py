from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Reflect the input horizontally and place the reflection to its right."""
    return [row + row[::-1] for row in grid]
