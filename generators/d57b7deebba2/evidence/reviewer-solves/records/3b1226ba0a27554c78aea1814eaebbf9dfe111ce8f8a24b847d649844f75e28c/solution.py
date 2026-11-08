from copy import deepcopy


def solve(grid):
    """Fill each same-color anti-diagonal span independently."""
    out = deepcopy(grid)
    groups = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                groups.setdefault((color, r + c), []).append((r, c))
    for (color, diagonal), cells in groups.items():
        if len(cells) < 2:
            continue
        lo = min(r for r, _ in cells)
        hi = max(r for r, _ in cells)
        for r in range(lo, hi + 1):
            c = diagonal - r
            if 0 <= c < len(grid[0]):
                out[r][c] = color
    return out
