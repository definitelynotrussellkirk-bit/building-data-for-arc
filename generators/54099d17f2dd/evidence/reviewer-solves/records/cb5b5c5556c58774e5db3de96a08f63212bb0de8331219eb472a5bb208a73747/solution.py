"""Visible-example solution for task 54099d17f2dd."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    marker = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    )
    template = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    top = min(r for r, _ in template)
    left = min(c for _, c in template)
    output = [[0] * width for _ in range(height)]
    for r, c in template:
        dr, dc = r - top, c - left
        output[marker[0] + dr][marker[1] + dc] = 8
    return output
