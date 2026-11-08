"""Visible-example solution for reviewer solve episode 7e19bce9c44c."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop away all-zero outer rows and columns.

    Internal zero cells are preserved; every nonzero colour participates in the
    same tight bounding box.
    """
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return []
    top = min(row for row, _col in cells)
    bottom = max(row for row, _col in cells)
    left = min(col for _row, col in cells)
    right = max(col for _row, col in cells)
    return [
        list(row[left:right + 1])
        for row in grid[top:bottom + 1]
    ]
