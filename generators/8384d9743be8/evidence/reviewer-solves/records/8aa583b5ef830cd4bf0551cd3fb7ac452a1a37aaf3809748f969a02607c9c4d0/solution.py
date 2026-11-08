from __future__ import annotations


def solve(grid):
    """Build union/intersection/xor panels from the aligned 5x5 masks."""
    if not isinstance(grid, list) or len(grid) != 5:
        raise ValueError("expected five rows")
    if any(not isinstance(row, list) or len(row) != 11 for row in grid):
        raise ValueError("expected an exact 5x11 grid")

    output = [[0] * 17 for _ in range(5)]
    for row in range(5):
        for column in range(5):
            left = grid[row][column] != 0
            right = grid[row][column + 6] != 0
            if left or right:
                output[row][column] = 2
            if left and right:
                output[row][column + 6] = 3
            if left != right:
                output[row][column + 12] = 4
    return output
