from __future__ import annotations

from collections import defaultdict
from copy import deepcopy


def solve(grid):
    """Connect consecutive complete red diamonds with blue segments."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = deepcopy(grid)
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if (grid[r - 1][c] == 2 and grid[r + 1][c] == 2
                    and grid[r][c - 1] == 2 and grid[r][c + 1] == 2):
                centers.append((r, c))

    by_row = defaultdict(list)
    by_col = defaultdict(list)
    for r, c in centers:
        by_row[r].append(c)
        by_col[c].append(r)

    for r, columns in by_row.items():
        columns.sort()
        for left, right in zip(columns, columns[1:]):
            for c in range(left + 1, right):
                if out[r][c] == 0:
                    out[r][c] = 1

    for c, rows in by_col.items():
        rows.sort()
        for top, bottom in zip(rows, rows[1:]):
            for r in range(top + 1, bottom):
                if out[r][c] == 0:
                    out[r][c] = 1
    return out
