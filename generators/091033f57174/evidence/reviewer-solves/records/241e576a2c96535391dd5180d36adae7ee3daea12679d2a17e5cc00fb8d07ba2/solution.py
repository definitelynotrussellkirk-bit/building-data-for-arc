"""Visible-example solution for the post-repair Commanded L-Links lesson."""
from __future__ import annotations

from collections import OrderedDict


def solve(grid):
    out = [row[:] for row in grid]
    command = grid[0][0]

    # Preserve first-appearance order because later routed colours visibly win
    # at any crossing.
    points = OrderedDict()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0 and value not in points:
                points[value] = []
            if value != 0:
                points[value].append((r, c))

    for colour, cells in points.items():
        if colour == command or len(cells) != 2:
            continue
        a, b = sorted(cells)
        if command == 1:
            for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                out[a[0]][c] = colour
            for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
                out[r][b[1]] = colour
        else:
            for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
                out[r][a[1]] = colour
            for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                out[b[0]][c] = colour
    return out
