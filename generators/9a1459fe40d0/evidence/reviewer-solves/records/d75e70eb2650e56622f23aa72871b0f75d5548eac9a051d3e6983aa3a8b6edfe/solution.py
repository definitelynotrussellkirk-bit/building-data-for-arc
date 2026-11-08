from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay the two halves around the vertical 8-divider using XOR.

    The left half is reflected onto the right half.  A right-side cell is
    painted 7 exactly when one, but not both, of the reflected-left and
    original-right cells is non-background.  All other cells are cleared.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected exactly one full-height divider column of 8s")

    divider = divider_columns[0]
    if divider * 2 + 1 != width:
        raise ValueError("expected equal-width halves around the divider")

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for right_col in range(divider + 1, width):
            left_col = 2 * divider - right_col
            left_filled = grid[row][left_col] != 0
            right_filled = grid[row][right_col] != 0
            if left_filled != right_filled:
                output[row][right_col] = 7

    return output
