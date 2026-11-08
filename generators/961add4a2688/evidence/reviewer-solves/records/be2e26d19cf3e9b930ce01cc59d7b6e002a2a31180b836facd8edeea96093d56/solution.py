"""Visible-only solver for the prepared 961add4a2688 episode."""
from __future__ import annotations


def solve(grid):
    rows = len(grid)
    cols = len(grid[0])
    frame = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not frame:
        raise ValueError("expected a color-8 rectangular frame")
    r0 = min(r for r, _ in frame)
    r1 = max(r for r, _ in frame)
    c0 = min(c for _, c in frame)
    c1 = max(c for _, c in frame)

    out = [[0] * cols for _ in range(rows)]
    for c in range(c0, c1 + 1):
        out[r0][c] = 8
        out[r1][c] = 8
    for r in range(r0, r1 + 1):
        out[r][c0] = 8
        out[r][c1] = 8

    for c in range(c0 + 1, c1):
        values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
        for offset, value in enumerate(values):
            out[r0 + 1 + offset][c] = value
    return out
