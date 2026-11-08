from copy import deepcopy


def solve(grid):
    """Complete empty mirror targets across the unique full-height 5 guide."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not dividers:
        return out
    divider = dividers[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5) or c == divider:
                continue
            mirror = 2 * divider - c
            if 0 <= mirror < w and out[r][mirror] == 0:
                out[r][mirror] = value
    return out
