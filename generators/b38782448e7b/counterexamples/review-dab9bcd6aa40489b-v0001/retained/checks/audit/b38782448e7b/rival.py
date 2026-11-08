"""Audit rival: toggle marked columns, rebuilding the rest on background.

This intentionally wrong solver ignores preservation of non-marker body cells.
It is not a proposed reference implementation.
"""
from collections import Counter


def solve(grid):
    h, w = len(grid), len(grid[0])
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    output = [[bg] * w for _ in range(h)]
    output[0] = grid[0][:]
    for c, marker in enumerate(grid[0]):
        if marker != bg and (h < 2 or marker != grid[1][c]):
            for r in range(1, h):
                output[r][c] = bg if grid[r][c] == marker else marker
    return output
