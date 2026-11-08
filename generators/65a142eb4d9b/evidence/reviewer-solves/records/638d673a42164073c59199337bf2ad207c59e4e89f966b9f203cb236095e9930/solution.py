"""Visible-example solution for the generated plus-expansion lesson."""
from __future__ import annotations


def solve(grid):
    """Expand each nonzero 4-neighbor singleton into an in-bounds plus."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            same_color_cardinal = any(
                0 <= row + drow < height
                and 0 <= col + dcol < width
                and grid[row + drow][col + dcol] == color
                for drow, dcol in directions
            )
            if same_color_cardinal:
                continue
            output[row][col] = color
            for drow, dcol in directions:
                next_row, next_col = row + drow, col + dcol
                if 0 <= next_row < height and 0 <= next_col < width:
                    output[next_row][next_col] = color
    return output
