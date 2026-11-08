"""Visible-example solution for 2dbcb80623f9."""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


def solve(grid):
    original = [list(row) for row in grid]
    out = deepcopy(original)
    positions = defaultdict(list)
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for color, cells in positions.items():
        for i, (r1, c1) in enumerate(cells):
            for r2, c2 in cells[i + 1:]:
                dr, dc = r2 - r1, c2 - c1
                if dr == 0 or abs(dr) != abs(dc):
                    continue
                sr = 1 if dr > 0 else -1
                sc = 1 if dc > 0 else -1
                path = []
                r, c = r1, c1
                while True:
                    path.append((r, c))
                    if (r, c) == (r2, c2):
                        break
                    r += sr
                    c += sc
                if all(original[r][c] == 0 for r, c in path[1:-1]):
                    for r, c in path:
                        out[r][c] = color
    return out
