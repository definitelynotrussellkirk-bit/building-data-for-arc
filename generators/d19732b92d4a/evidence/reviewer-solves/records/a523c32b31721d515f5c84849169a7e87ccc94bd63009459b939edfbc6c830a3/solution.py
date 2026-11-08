from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the blank midpoint of each length-2 same-color diagonal pair.

    Only cells from the original grid define pairs, and occupied midpoints are
    left unchanged.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for row in range(height - 2):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for delta_col in (-2, 2):
                other_col = col + delta_col
                if not 0 <= other_col < width:
                    continue
                if grid[row + 2][other_col] != color:
                    continue
                mid_col = col + delta_col // 2
                if grid[row + 1][mid_col] == 0:
                    out[row + 1][mid_col] = color

    return out
