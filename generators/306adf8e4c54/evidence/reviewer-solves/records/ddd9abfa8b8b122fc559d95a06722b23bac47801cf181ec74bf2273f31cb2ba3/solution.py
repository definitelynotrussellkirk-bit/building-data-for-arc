from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the center cell of every horizontal or vertical 4,0,4 motif."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    original = [row[:] for row in grid]
    result = [row[:] for row in grid]

    for r in range(height):
        for c in range(width - 2):
            if original[r][c : c + 3] == [4, 0, 4]:
                result[r][c + 1] = 4

    for r in range(height - 2):
        for c in range(width):
            if [original[r + offset][c] for offset in range(3)] == [4, 0, 4]:
                result[r + 1][c] = 4

    return result
