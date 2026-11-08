"""Complete monochrome pluses using only a snapshot of the input."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError('expected a nonempty rectangular grid')
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError('expected equally sized rows')
    source = [row[:] for row in grid]
    result = [row[:] for row in grid]
    for row in range(1, len(source) - 1):
        for col in range(1, width - 1):
            color = source[row][col]
            if color == 0:
                continue
            neighbors = (source[row - 1][col], source[row + 1][col],
                         source[row][col - 1], source[row][col + 1])
            if all(value == color for value in neighbors):
                for rr in range(row - 1, row + 2):
                    for cc in range(col - 1, col + 2):
                        result[rr][cc] = color
    return result
