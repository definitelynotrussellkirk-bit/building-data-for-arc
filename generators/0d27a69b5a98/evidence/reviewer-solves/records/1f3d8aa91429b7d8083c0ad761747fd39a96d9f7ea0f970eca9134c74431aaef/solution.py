"""Visible-example solution for the post-repair solve episode."""
from __future__ import annotations


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    full_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    full_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    out = [row[:] for row in grid]
    original = [row[:] for row in grid]
    if full_cols:
        axis = full_cols[0]
        for r, row in enumerate(original):
            for c, value in enumerate(row):
                if value not in (0, 9):
                    mc = 2 * axis - c
                    if 0 <= mc < w:
                        out[r][mc] = value
    elif full_rows:
        axis = full_rows[0]
        for r, row in enumerate(original):
            for c, value in enumerate(row):
                if value not in (0, 9):
                    mr = 2 * axis - r
                    if 0 <= mr < h:
                        out[mr][c] = value
    return out
