"""Public-example-derived solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid):
    """Floor-center the nonzero bounding box, preserving exact cell contents."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not cells:
        return [list(row) for row in grid]

    row0 = min(row for row, _, _ in cells)
    row1 = max(row for row, _, _ in cells)
    col0 = min(col for _, col, _ in cells)
    col1 = max(col for _, col, _ in cells)
    bbox_height = row1 - row0 + 1
    bbox_width = col1 - col0 + 1
    target_row = (height - bbox_height) // 2
    target_col = (width - bbox_width) // 2
    delta_row = target_row - row0
    delta_col = target_col - col0

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col, value in cells:
        output[row + delta_row][col + delta_col] = value
    return output
