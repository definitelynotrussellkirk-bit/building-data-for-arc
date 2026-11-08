def solve(grid):
    """Fill the color-8 chamber by Manhattan-nearest colored seed."""
    out = [list(row) for row in grid]
    frame = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not frame:
        return out

    r0 = min(r for r, _c in frame)
    c0 = min(c for _r, c in frame)
    r1 = max(r for r, _c in frame)
    c1 = max(c for _r, c in frame)
    seeds = sorted(
        (r, c, grid[r][c])
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] not in (0, 8)
    )

    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if grid[r][c] != 0 or not seeds:
                continue
            _distance, _sr, _sc, color = min(
                (
                    abs(r - sr) + abs(c - sc),
                    sr,
                    sc,
                    color,
                )
                for sr, sc, color in seeds
            )
            out[r][c] = color
    return out
