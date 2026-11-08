"""Visible-example solution for the prepared reviewer episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Intersect the two equal panels separated by the full color-5 row."""
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    width = len(grid[0])
    dividers = [
        index for index, row in enumerate(grid)
        if len(row) == width and all(value == 5 for value in row)
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected one full color-5 divider, got {dividers}")
    divider = dividers[0]
    top = grid[:divider]
    bottom = grid[divider + 1 :]
    if len(top) != len(bottom):
        raise ValueError("divider does not split equal-height panels")
    return [
        [
            8 if top[row][column] != 0 and bottom[row][column] != 0 else 0
            for column in range(width)
        ]
        for row in range(len(top))
    ]
