"""Visible-example solution for d5d9fdb01bdd."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("input has no nonzero content")
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    crop = [values[left : right + 1] for values in grid[top : bottom + 1]]
    return [list(column) for column in zip(*crop)]
