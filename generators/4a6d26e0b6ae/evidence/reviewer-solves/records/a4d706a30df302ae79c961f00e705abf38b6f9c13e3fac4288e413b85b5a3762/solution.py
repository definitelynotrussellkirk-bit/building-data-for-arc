"""Fill observed one-cell orthogonal gaps, preserving all original endpoints.

Authored from the visible example pairs during a declared earlier-exposure
review solve. No generator, reference code, or hidden labels are imported.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError('Expected a nonempty rectangular grid')
    if not all(isinstance(row, (list, tuple)) for row in grid):
        raise ValueError('Rows must be integer sequences')
    width = len(grid[0])
    if not width or any(len(row) != width for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError('Grid values must be integer colors 0..9')
    height = len(grid)
    result = [list(row) for row in grid]
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 0:
                continue
            candidates = set()
            if 0 < c < width - 1 and grid[r][c-1] != 0 and grid[r][c-1] == grid[r][c+1]:
                candidates.add(grid[r][c-1])
            if 0 < r < height - 1 and grid[r-1][c] != 0 and grid[r-1][c] == grid[r+1][c]:
                candidates.add(grid[r-1][c])
            if len(candidates) > 1:
                raise ValueError('Visible examples do not identify a conflicting-axis priority')
            if candidates:
                result[r][c] = next(iter(candidates))
    return result
