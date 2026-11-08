def solve(grid):
    """Add a yellow cell one step down-left from every gray cell when empty."""
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 9:
                continue
            rr, cc = r + 1, c - 1
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0:
                out[rr][cc] = 5
    return out
