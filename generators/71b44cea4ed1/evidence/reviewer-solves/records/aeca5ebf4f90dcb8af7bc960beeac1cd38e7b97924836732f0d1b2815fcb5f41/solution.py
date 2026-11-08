from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill blank midpoints of equal-color 2-by-2 diagonal endpoints."""
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    output = [row[:] for row in grid]
    # Read only from the original input so newly painted cells cannot trigger
    # a second, unintended wave of fills.
    for row in range(height - 2):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for delta_col in (-2, 2):
                end_col = col + delta_col
                if not 0 <= end_col < width:
                    continue
                mid_row = row + 1
                mid_col = col + delta_col // 2
                if (
                    grid[row + 2][end_col] == color
                    and grid[mid_row][mid_col] == 0
                ):
                    output[mid_row][mid_col] = color
    return output
