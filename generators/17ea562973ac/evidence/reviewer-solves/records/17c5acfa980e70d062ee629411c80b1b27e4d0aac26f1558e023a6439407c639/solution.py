"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid):
    h = len(grid)
    w = len(grid[0])
    cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not cells:
        return [[0 for _ in range(w)] for _ in range(h)]
    color = cells[0][2]
    r1 = min(r for r, _, _ in cells)
    r2 = max(r for r, _, _ in cells)
    c1 = min(c for _, c, _ in cells)
    c2 = max(c for _, c, _ in cells)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for c in range(c1, c2 + 1):
        out[r1][c] = color
        out[r2][c] = color
    for r in range(r1, r2 + 1):
        out[r][c1] = color
        out[r][c2] = color
    return out
