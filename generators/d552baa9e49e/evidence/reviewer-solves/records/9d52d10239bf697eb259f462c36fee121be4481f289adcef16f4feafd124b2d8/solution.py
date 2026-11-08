def solve(grid):
    """Crop the payload and rotate it clockwise by the top-left marker count."""
    turns = grid[0][0] % 4

    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    if not cells:
        return []

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    out = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    for _ in range(turns):
        out = [list(row) for row in zip(*out[::-1])]
    return out
