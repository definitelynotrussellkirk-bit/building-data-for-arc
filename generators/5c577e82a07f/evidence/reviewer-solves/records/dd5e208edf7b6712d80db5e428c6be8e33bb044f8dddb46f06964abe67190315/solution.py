from __future__ import annotations

from collections import defaultdict


def solve(grid):
    """Complete the axis-aligned rectangle border encoded by each color's corners."""
    out = [list(row) for row in grid]
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color[value].append((r, c))

    for color, cells in by_color.items():
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(rows) != 2 or len(cols) != 2:
            continue
        r0, r1 = rows
        c0, c1 = cols
        corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
        if set(cells) != corners:
            continue
        for c in range(c0, c1 + 1):
            out[r0][c] = color
            out[r1][c] = color
        for r in range(r0, r1 + 1):
            out[r][c0] = color
            out[r][c1] = color
    return out
