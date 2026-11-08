"""Complete qualifying 2x2 corners once, reading only the original grid."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid entries must be integer colours 0..9")
    answer = [row[:] for row in grid]
    for row in range(len(grid) - 1):
        for col in range(width - 1):
            positions = ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
            values = [grid[r][c] for r, c in positions]
            if values.count(0) != 1:
                continue
            occupied = [value for value in values if value != 0]
            if occupied[0] == occupied[1] == occupied[2]:
                r, c = positions[values.index(0)]
                answer[r][c] = occupied[0]
    return answer
