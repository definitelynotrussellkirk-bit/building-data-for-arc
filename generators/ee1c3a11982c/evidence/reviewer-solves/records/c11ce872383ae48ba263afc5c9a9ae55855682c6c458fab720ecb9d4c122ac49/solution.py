"""Solution inferred from the three visible demonstrations.

Earlier exposure during generator review is declared in the solve metadata.
No generator, Racket reference, or private labels are imported here.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('expected integer colors in 0..9')
    result = []
    last_column_color = 0
    for row in grid:
        latest = 0
        painted = []
        for color in row:
            if color:
                latest = color
            painted.append(latest)
        if latest:
            last_column_color = latest
        painted[-1] = last_column_color
        result.append(painted)
    return result
