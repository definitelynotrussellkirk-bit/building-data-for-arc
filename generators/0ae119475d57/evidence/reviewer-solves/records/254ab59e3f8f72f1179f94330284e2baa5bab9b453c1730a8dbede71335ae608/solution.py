"""Align the panels around the central separator; nonzero lower cells win."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or len(grid) < 3 or len(grid) % 2 != 1:
        raise ValueError('Expected two equally tall panels and one separator row')
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError('Expected nonempty rows')
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError('Expected a rectangular grid')
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError('Expected integer grid colors')
    middle = len(grid) // 2
    if grid[middle][0] == 0 or len(set(grid[middle])) != 1:
        raise ValueError('Expected a uniform nonzero central separator')
    return [
        [grid[middle + 1 + r][c] or grid[r][c] for c in range(width)]
        for r in range(middle)
    ]
