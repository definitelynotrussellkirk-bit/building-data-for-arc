"""Visible-example solver for reviewer solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the body object whose color is named by the top-row marker.

    The output is the unmodified rectangular slice spanning all occurrences
    of the marker color below the blank separator row. Other colors that fall
    inside that rectangle are retained.
    """
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    markers = [value for value in grid[0] if value != 0]
    if len(markers) != 1:
        raise ValueError("expected exactly one nonzero top-row marker")
    guide = markers[0]

    cells = [
        (row, col)
        for row in range(1, len(grid))
        for col in range(width)
        if grid[row][col] == guide
    ]
    if not cells:
        raise ValueError("marker color is absent from the body")

    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
