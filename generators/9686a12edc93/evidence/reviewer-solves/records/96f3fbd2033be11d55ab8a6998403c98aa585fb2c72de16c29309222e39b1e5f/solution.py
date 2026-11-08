"""Visible-example solution for task 9686a12edc93."""
from __future__ import annotations

from collections import defaultdict


def solve(grid):
    """Draw clear axis-aligned exactly-two color pairs on an empty output."""
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]

    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            lo, hi = sorted((c1, c2))
            if all(grid[r1][c] == 0 for c in range(lo + 1, hi)):
                for c in range(lo, hi + 1):
                    out[r1][c] = color
        elif c1 == c2:
            lo, hi = sorted((r1, r2))
            if all(grid[r][c1] == 0 for r in range(lo + 1, hi)):
                for r in range(lo, hi + 1):
                    out[r][c1] = color
    return out
