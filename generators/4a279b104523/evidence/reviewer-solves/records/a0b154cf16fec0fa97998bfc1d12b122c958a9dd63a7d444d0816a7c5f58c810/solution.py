"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid):
    """Copy every nonzero non-8 cell across the unique full row of 8s."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    width = len(grid[0])
    axes = [r for r, row in enumerate(grid) if len(row) == width and all(v == 8 for v in row)]
    if len(axes) != 1:
        raise ValueError(f"expected one full row of 8s, found {len(axes)}")
    axis = axes[0]
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        if r == axis:
            continue
        for c, value in enumerate(row):
            if value in (0, 8):
                continue
            reflected = 2 * axis - r
            if 0 <= reflected < len(grid):
                out[reflected][c] = value
    return out
