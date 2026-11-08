"""Visible-example solution for task 38200022d1b7."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy each colored source through a 180-degree rotation around color 5."""
    out = [row[:] for row in grid]
    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected exactly one color-5 pivot, found {len(pivots)}")
    pr, pc = pivots[0]
    height = len(grid)
    width = len(grid[0]) if grid else 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5):
                continue
            rr, cc = 2 * pr - r, 2 * pc - c
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value
    return out
