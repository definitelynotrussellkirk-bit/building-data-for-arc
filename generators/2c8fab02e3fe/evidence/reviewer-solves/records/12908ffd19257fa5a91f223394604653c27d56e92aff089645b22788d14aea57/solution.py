"""Visible-example solution for the prepared ARC episode."""
from __future__ import annotations

from collections import Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the interior of the color-8 rectangle with the singleton color."""
    counts = Counter(value for row in grid for value in row)
    singleton_colors = [
        color for color, count in counts.items()
        if color not in (0, 8) and count == 1
    ]
    if len(singleton_colors) != 1:
        raise ValueError(f"expected one non-background singleton, got {singleton_colors}")
    fill = singleton_colors[0]

    frame = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 8
    ]
    if not frame:
        raise ValueError("missing color-8 frame")

    top = min(row for row, _ in frame)
    bottom = max(row for row, _ in frame)
    left = min(col for _, col in frame)
    right = max(col for _, col in frame)

    result = [list(row) for row in grid]
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            result[row][col] = fill
    return result
