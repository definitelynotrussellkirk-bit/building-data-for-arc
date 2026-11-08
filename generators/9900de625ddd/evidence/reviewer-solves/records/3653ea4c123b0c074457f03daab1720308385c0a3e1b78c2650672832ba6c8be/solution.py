from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep exactly the nonzero cells with a same-colour 3x3 neighbourhood."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    for row in range(1, height - 1):
        for col in range(1, width - 1):
            colour = grid[row][col]
            if colour == 0:
                continue
            if all(
                grid[near_row][near_col] == colour
                for near_row in range(row - 1, row + 2)
                for near_col in range(col - 1, col + 2)
            ):
                output[row][col] = colour

    return output
