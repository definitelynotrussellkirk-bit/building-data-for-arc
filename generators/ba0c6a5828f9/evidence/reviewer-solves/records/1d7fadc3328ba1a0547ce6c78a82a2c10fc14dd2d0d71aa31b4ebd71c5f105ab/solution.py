"""Visible-example solution for ba0c6a5828f9."""
from __future__ import annotations


def solve(grid):
    """Complete each blue marker's quarter-turn orbit around the red pivot."""
    out = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])
    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected one red pivot, found {len(pivots)}")
    pr, pc = pivots[0]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    for r, c in markers:
        dr, dc = r - pr, c - pc
        for rr, cc in (
            (pr + dr, pc + dc),
            (pr + dc, pc - dr),
            (pr - dr, pc - dc),
            (pr - dc, pc + dr),
        ):
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = 1
    return out
