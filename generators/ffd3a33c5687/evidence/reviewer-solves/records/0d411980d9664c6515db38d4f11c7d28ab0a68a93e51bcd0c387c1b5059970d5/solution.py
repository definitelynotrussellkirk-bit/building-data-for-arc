from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete each row's left/right mirror pairs; a nonzero left cell wins ties."""
    output = [row[:] for row in grid]
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            color = row[left_col] if row[left_col] != 0 else row[right_col]
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output
