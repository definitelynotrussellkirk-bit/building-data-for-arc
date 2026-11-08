"""Visible-only solution for the prepared 97d3714964b0 episode."""
from __future__ import annotations


def solve(grid):
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 7
    }

    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in remaining:
                    remaining.remove((rr, cc))
                    cells.add((rr, cc))
                    stack.append((rr, cc))

        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        has_empty_interior = any(
            grid[r][c] == 0 and (r, c) not in cells
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        )
        color = 4 if has_empty_interior else 2
        for r, c in cells:
            out[r][c] = color

    return out
