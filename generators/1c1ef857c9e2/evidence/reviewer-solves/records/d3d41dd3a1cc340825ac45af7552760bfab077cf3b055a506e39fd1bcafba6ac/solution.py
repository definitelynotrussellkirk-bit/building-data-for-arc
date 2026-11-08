"""Visible-example solution for the generated ARC task."""

from __future__ import annotations

from collections import Counter
from typing import Sequence

Grid = list[list[int]]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Count complete separator rows/columns and encode the cell layout.

    The majority color is the background/output color.  The other color forms
    complete horizontal and vertical separator lines.  N horizontal lines
    divide the plane into N+1 row regions, and M vertical lines divide it into
    M+1 column regions, so the answer is an (N+1) x (M+1) solid background grid.
    """
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    separator_colors = [color for color in counts if color != background]
    if len(separator_colors) != 1:
        raise ValueError("expected exactly one non-background separator color")
    separator = separator_colors[0]

    horizontal = sum(all(value == separator for value in row) for row in grid)
    vertical = sum(
        all(grid[row_index][column_index] == separator for row_index in range(len(grid)))
        for column_index in range(width)
    )

    return [[background] * (vertical + 1) for _ in range(horizontal + 1)]
