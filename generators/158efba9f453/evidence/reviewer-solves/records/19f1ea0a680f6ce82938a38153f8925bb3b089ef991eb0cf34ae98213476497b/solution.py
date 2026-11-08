"""Visible-example solution for the prepared ARC challenge."""

from __future__ import annotations

from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Mirror each non-background, non-marker cell across the gray-marker column.

    The visible examples contain two gray (5) cells in one column.  That
    column is the vertical reflection axis.  The original grid is preserved,
    and every colored motif cell is copied to its reflected column.
    """
    if not grid:
        raise ValueError("grid must contain at least one row")

    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    marker_columns = {
        column
        for row in grid
        for column, value in enumerate(row)
        if value == 5
    }
    if len(marker_columns) != 1:
        raise ValueError("gray markers must identify exactly one vertical axis")
    axis_column = next(iter(marker_columns))

    result = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for column, value in enumerate(row):
            if value in (0, 5):
                continue
            reflected_column = 2 * axis_column - column
            if 0 <= reflected_column < width:
                result[row_index][reflected_column] = value

    return result
