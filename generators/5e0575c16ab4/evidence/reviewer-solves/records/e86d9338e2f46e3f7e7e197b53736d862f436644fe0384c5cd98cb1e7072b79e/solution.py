def solve(grid):
    """Fill every unobstructed horizontal segment delimited by a unique color pair."""
    out = [list(row) for row in grid]
    positions = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 != r2:
            continue
        left, right = sorted((c1, c2))
        if all(grid[r1][c] == 0 for c in range(left + 1, right)):
            for c in range(left, right + 1):
                out[r1][c] = color
    return out
