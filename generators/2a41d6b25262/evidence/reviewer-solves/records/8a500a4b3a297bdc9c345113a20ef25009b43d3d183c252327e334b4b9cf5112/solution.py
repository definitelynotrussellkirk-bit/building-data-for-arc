"""Visible-example solution for task 2a41d6b25262."""
from __future__ import annotations


def _cells(grid, color):
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }


def _normalize(points):
    if not points:
        return set()
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return {(row - top, col - left) for row, col in points}


def solve(grid):
    """Stamp the normalized symmetric difference of colors 2 and 3 at color 1."""
    red = _normalize(_cells(grid, 2))
    green = _normalize(_cells(grid, 3))
    markers = sorted(_cells(grid, 1))
    if len(markers) != 1:
        raise ValueError(f"expected one color-1 marker, found {len(markers)}")

    output = [[0 for _ in row] for row in grid]
    anchor_row, anchor_col = markers[0]
    for dr, dc in red ^ green:
        row, col = anchor_row + dr, anchor_col + dc
        if not (0 <= row < len(output) and 0 <= col < len(output[0])):
            raise ValueError("derived stamp leaves the output grid")
        output[row][col] = 8
    return output
