"""Visible-example solution for the frozen generator episode."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy every colored cell left of the full-height 5 divider to its mirror."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    divider_candidates = [
        col for col in range(width)
        if all(row[col] == 5 for row in grid)
    ]
    if len(divider_candidates) != 1:
        raise ValueError("expected one full-height color-5 divider")

    divider = divider_candidates[0]
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for col in range(divider):
            color = row[col]
            if color in (0, 5):
                continue
            reflected_col = 2 * divider - col
            if not 0 <= reflected_col < width:
                raise ValueError("reflected position is outside the grid")
            output[row_index][reflected_col] = color
    return output


transform = solve
solution = solve
