from copy import deepcopy


def solve(grid):
    """Trace the color-2 beam, painting zero cells 7 until wall/boundary."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    source = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    r, c = source
    # Visible corner example shows top/bottom precedence over left/right.
    if r == 0:
        dr, dc = 1, 0
    elif r == h - 1:
        dr, dc = -1, 0
    elif c == 0:
        dr, dc = 0, 1
    else:
        dr, dc = 0, -1

    for _ in range(4 * h * w):
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w):
            break
        value = grid[nr][nc]
        if value == 8:
            break
        if value == 4:
            dr, dc = -dc, -dr
        elif value == 5:
            dr, dc = dc, dr
        elif value == 0:
            out[nr][nc] = 7
        r, c = nr, nc
    return out
