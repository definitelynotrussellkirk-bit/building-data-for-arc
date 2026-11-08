from copy import deepcopy


def solve(grid):
    nonzero = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not nonzero:
        return deepcopy(grid)

    r0 = min(r for r, _ in nonzero)
    r1 = max(r for r, _ in nonzero)
    c0 = min(c for _, c in nonzero)
    c1 = max(c for _, c in nonzero)

    marked_rows = [r for r in range(r0 + 1, r1) if grid[r][c0] == 2]
    marked_cols = [c for c in range(c0 + 1, c1) if grid[r0][c] == 3]

    out = deepcopy(grid)
    for r in marked_rows:
        for c in marked_cols:
            out[r][c] = 7
    return out
