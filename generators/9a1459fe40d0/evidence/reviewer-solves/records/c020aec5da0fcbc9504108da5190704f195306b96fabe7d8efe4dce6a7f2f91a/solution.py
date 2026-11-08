from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Mirror the left mask across the 8-divider and XOR it with the right mask."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_candidates = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(divider_candidates) != 1:
        raise ValueError("expected exactly one full-height color-8 divider")

    divider = divider_candidates[0]
    if divider * 2 + 1 != width:
        raise ValueError("divider must split the grid into equal-width halves")

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for right_col in range(divider + 1, width):
            left_col = 2 * divider - right_col
            left_occupied = grid[row][left_col] != 0
            right_occupied = grid[row][right_col] != 0
            if left_occupied != right_occupied:
                output[row][right_col] = 7

    return output
