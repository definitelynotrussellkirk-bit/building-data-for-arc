"""Visible-example solver for the crossing-bars transformation."""
from __future__ import annotations

from copy import deepcopy
from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Swap the complete crossing rectangle to the rear bar's color."""
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    full_rows = [
        row for row in range(height) if all(grid[row][col] != 0 for col in range(width))
    ]
    full_cols = [
        col for col in range(width) if all(grid[row][col] != 0 for row in range(height))
    ]
    if not full_rows or not full_cols:
        raise ValueError("expected one full-width and one full-height nonzero bar")

    row_set = set(full_rows)
    col_set = set(full_cols)
    horizontal_colors = {
        grid[row][col]
        for row in full_rows
        for col in range(width)
        if col not in col_set
    }
    vertical_colors = {
        grid[row][col]
        for col in full_cols
        for row in range(height)
        if row not in row_set
    }
    if len(horizontal_colors) != 1 or len(vertical_colors) != 1:
        raise ValueError("bar flanks must each have one color")

    horizontal_color = next(iter(horizontal_colors))
    vertical_color = next(iter(vertical_colors))
    overlap_color = grid[full_rows[0]][full_cols[0]]
    if overlap_color == horizontal_color:
        replacement = vertical_color
    elif overlap_color == vertical_color:
        replacement = horizontal_color
    else:
        raise ValueError("overlap must have one bar's color")

    output = deepcopy([list(row) for row in grid])
    for row in full_rows:
        for col in full_cols:
            output[row][col] = replacement
    return output
