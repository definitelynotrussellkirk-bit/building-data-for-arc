def solve(grid):
    """Stamp a clipped orange diagonal X at every blue marker."""
    h = len(grid)
    w = len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = 7
    return out
