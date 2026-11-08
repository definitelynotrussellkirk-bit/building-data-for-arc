def solve(grid):
    """Fill a blank center when its four cardinal neighbors share a color."""
    out = [list(row) for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            color = grid[r - 1][c]
            if color and all(grid[rr][cc] == color for rr, cc in
                             ((r + 1, c), (r, c - 1), (r, c + 1))):
                out[r][c] = color
    return out
