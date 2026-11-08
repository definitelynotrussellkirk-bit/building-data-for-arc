from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Upscale each cell by the number of distinct colors in the input."""
    scale = len({value for row in grid for value in row})
    return [
        [value for value in row for _ in range(scale)]
        for row in grid
        for _ in range(scale)
    ]
