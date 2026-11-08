"""Visible-example solution for the prepared b19deac47327 episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    top_solid = len(set(grid[0])) == 1 and grid[0][0] not in (0, 1)
    bottom_solid = len(set(grid[-1])) == 1 and grid[-1][0] not in (0, 1)
    left_values = [row[0] for row in grid]
    right_values = [row[-1] for row in grid]
    left_solid = len(set(left_values)) == 1 and left_values[0] not in (0, 1)
    right_solid = len(set(right_values)) == 1 and right_values[0] not in (0, 1)

    if top_solid and bottom_solid:
        first_color, second_color = grid[0][0], grid[-1][0]
        for row in range(height):
            for col in range(width):
                if grid[row][col] != 1:
                    continue
                first_half = 2 * row < height
                target_row = row - 1 if first_half else row + 1
                if 0 <= target_row < height:
                    out[target_row][col] = first_color if first_half else second_color
        return out

    if left_solid and right_solid:
        first_color, second_color = grid[0][0], grid[0][-1]
        for row in range(height):
            for col in range(width):
                if grid[row][col] != 1:
                    continue
                first_half = 2 * col < width
                target_col = col - 1 if first_half else col + 1
                if 0 <= target_col < width:
                    out[row][target_col] = first_color if first_half else second_color
        return out

    return out
