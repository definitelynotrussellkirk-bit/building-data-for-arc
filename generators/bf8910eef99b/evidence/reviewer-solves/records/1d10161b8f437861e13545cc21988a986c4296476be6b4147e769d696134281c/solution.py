"""Visible-example solution for bf8910eef99b."""
from copy import deepcopy


def solve(grid):
    h, w = len(grid), len(grid[0])
    br = bc = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                br, bc = r, c
                break
        if br is not None:
            break
    if br is None or br + 1 >= h or bc + 1 >= w:
        return deepcopy(grid)
    tl, tr = grid[br][bc], grid[br][bc + 1]
    bl, brr = grid[br + 1][bc], grid[br + 1][bc + 1]
    out = deepcopy(grid)

    def paint(rows, cols, color):
        for r in rows:
            for c in cols:
                if 0 <= r < h and 0 <= c < w and out[r][c] == 0:
                    out[r][c] = color

    paint((br + 2, br + 3), (bc + 2, bc + 3), tl)
    paint((br + 2, br + 3), (bc - 2, bc - 1), tr)
    paint((br - 2, br - 1), (bc + 2, bc + 3), bl)
    paint((br - 2, br - 1), (bc - 2, bc - 1), brr)
    return out
