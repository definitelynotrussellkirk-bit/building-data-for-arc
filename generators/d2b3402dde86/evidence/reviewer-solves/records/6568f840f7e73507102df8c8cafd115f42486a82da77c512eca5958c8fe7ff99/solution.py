"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop to nonzero content, then return its upper-left floor-half."""
    if not grid or not grid[0]:
        raise ValueError("expected a non-empty rectangular grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("grid has no nonzero content")

    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    content_h = bottom - top + 1
    content_w = right - left + 1
    out_h = content_h // 2
    out_w = content_w // 2
    return [
        list(grid[row][left:left + out_w])
        for row in range(top, top + out_h)
    ]
