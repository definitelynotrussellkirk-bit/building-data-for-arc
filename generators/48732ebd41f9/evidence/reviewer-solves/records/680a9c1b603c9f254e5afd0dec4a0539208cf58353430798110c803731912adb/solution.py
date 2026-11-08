"""Visible-example solution for reviewer episode 48732ebd41f9."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the greatest-area all-zero rectangle of height at least two with 6.

    Ties are resolved by the first rectangle encountered in row-band order
    (smallest top row, then smallest bottom row, then leftmost run).
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    best: tuple[int, int, int, int] | None = None
    best_area = 0

    for top in range(height):
        valid_columns = [True] * width
        for bottom in range(top, height):
            for col in range(width):
                valid_columns[col] = valid_columns[col] and grid[bottom][col] == 0
            rect_height = bottom - top + 1
            if rect_height < 2:
                continue

            run_start: int | None = None
            for col in range(width + 1):
                if col < width and valid_columns[col]:
                    if run_start is None:
                        run_start = col
                    continue
                if run_start is not None:
                    right = col - 1
                    area = rect_height * (right - run_start + 1)
                    if area > best_area:
                        best_area = area
                        best = (top, run_start, bottom, right)
                    run_start = None

    output = [row[:] for row in grid]
    if best is None:
        return output
    top, left, bottom, right = best
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = 6
    return output
