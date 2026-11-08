"""Visible-example solution for dfc3ce537883."""
from __future__ import annotations


def solve(grid):
    if not grid or not grid[0]:
        return grid
    h, w = len(grid), len(grid[0])
    axes = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(axes) != 1:
        raise ValueError(f"expected one full color-9 divider, found {len(axes)}")
    axis = axes[0]
    out = [list(row) for row in grid]
    for r in range(h):
        for c in range(axis):
            color = grid[r][c]
            if color not in (0, 9):
                mirror = 2 * axis - c
                if 0 <= mirror < w:
                    out[r][mirror] = color
    return out
