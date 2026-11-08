"""Visible-example solution for the counted quarter-turn orbit task."""
from __future__ import annotations


def solve(grid):
    h = len(grid)
    w = len(grid[0])
    k = sum(value == 1 for value in grid[0])

    anchor = next(
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == 9
    )
    orbit_cells = [
        (row, col, grid[row][col])
        for row in range(1, h)
        for col in range(w)
        if grid[row][col] not in (0, 9)
    ]

    out = [[0 for _ in range(w)] for _ in range(h)]
    ar, ac = anchor
    out[ar][ac] = 9
    for row, col, color in orbit_cells:
        dr, dc = row - ar, col - ac
        for _ in range(k):
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = color
            dr, dc = dc, -dr
    return out
