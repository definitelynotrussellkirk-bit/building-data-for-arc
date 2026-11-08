"""Visible-example solve for the exposed projection task."""
from copy import deepcopy


def solve(grid):
    output = deepcopy(grid)
    cyan = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not cyan:
        return output
    rmin = min(r for r, _ in cyan)
    rmax = max(r for r, _ in cyan)
    cmin = min(c for _, c in cyan)
    cmax = max(c for _, c in cyan)

    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 8):
                continue
            if rmin <= r <= rmax:
                output[r][cmin if c < cmin else cmax] = color
            elif cmin <= c <= cmax:
                output[rmin if r < rmin else rmax][c] = color
    return output
