"""Visible-example solution for the reviewer solve episode."""
from collections import defaultdict


def solve(grid):
    out = [row[:] for row in grid]
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color[value].append((r, c))

    for color, cells in by_color.items():
        if len(cells) != 3:
            continue
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(rows) != 2 or len(cols) != 2:
            continue
        present = set(cells)
        missing = [
            (r, c)
            for r in rows
            for c in cols
            if (r, c) not in present
        ]
        if len(missing) == 1:
            r, c = missing[0]
            out[r][c] = color
    return out
