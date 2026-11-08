"""Visible-only solution for the blind ARC task.

Complete each row by reflecting every colored cell across the vertical axis.
The supplied examples contain no conflicting colored mirror pairs, so existing
colored cells are preserved and only blank mirror positions are filled.
"""


def solve(grid):
    out = [row[:] for row in grid]
    width = len(grid[0]) if grid else 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                mirror_c = width - 1 - c
                if out[r][mirror_c] == 0:
                    out[r][mirror_c] = value
    return out
