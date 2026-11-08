"""Visible-example solution for the post-repair episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    occupied = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0
    ]
    if not occupied:
        return []
    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    crop = [line[left:right + 1] for line in grid[top:bottom + 1]]
    return [line + line for line in crop]
