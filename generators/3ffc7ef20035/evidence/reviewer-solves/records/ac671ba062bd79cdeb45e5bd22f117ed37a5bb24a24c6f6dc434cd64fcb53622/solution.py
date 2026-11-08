"""Visible-example solution for the prepared ARC lesson."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the tight bounding rectangle of all blue (1) cells with cyan (8)."""
    output = [row[:] for row in grid]
    blue = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not blue:
        return output
    top = min(row for row, _col in blue)
    left = min(col for _row, col in blue)
    bottom = max(row for row, _col in blue)
    right = max(col for _row, col in blue)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = 8
    return output
