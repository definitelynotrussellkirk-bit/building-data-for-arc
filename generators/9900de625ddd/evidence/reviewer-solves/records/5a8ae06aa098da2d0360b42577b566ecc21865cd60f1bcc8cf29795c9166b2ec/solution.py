from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep only nonzero cells with an all-same-color 3x3 neighborhood."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    result = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            color = grid[row][col]
            if color == 0:
                continue
            if all(
                grid[r][c] == color
                for r in range(row - 1, row + 2)
                for c in range(col - 1, col + 2)
            ):
                result[row][col] = color
    return result
