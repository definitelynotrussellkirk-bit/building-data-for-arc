"""Visible-example solution for post-repair task aa378df15340."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy every nonzero cell to its main-diagonal transpose."""
    out = [row[:] for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                out[col][row] = value
    return out
