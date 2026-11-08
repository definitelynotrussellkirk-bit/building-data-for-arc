"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor the greatest-area solid zero rectangle of height >= 2 with 6."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    best: tuple[int, int, int, int] | None = None
    best_area = -1

    # For each top row, maintain which columns have stayed zero through the
    # current bottom row. Every maximal true run is a solid zero rectangle for
    # that row band. Strict '>' preserves the first scan-order rectangle on a
    # tie, though the visible lessons have unique winners.
    for top in range(height):
        all_zero = [True] * width
        for bottom in range(top, height):
            for col in range(width):
                all_zero[col] = all_zero[col] and grid[bottom][col] == 0

            rect_height = bottom - top + 1
            if rect_height < 2:
                continue

            start: int | None = None
            for col in range(width + 1):
                if col < width and all_zero[col]:
                    if start is None:
                        start = col
                    continue
                if start is None:
                    continue
                area = rect_height * (col - start)
                if area > best_area:
                    best_area = area
                    best = (top, start, bottom, col - 1)
                start = None

    result = [list(row) for row in grid]
    if best is None:
        return result

    top, left, bottom, right = best
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            result[row][col] = 6
    return result
