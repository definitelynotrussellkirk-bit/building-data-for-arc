def solve(grid):
    """Keep the first and last cell of every same-color vertical run."""
    if not grid:
        return []
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for c in range(w):
        r = 0
        while r < h:
            color = grid[r][c]
            if color == 0:
                r += 1
                continue
            start = r
            while r + 1 < h and grid[r + 1][c] == color:
                r += 1
            end = r
            out[start][c] = color
            out[end][c] = color
            r += 1
    return out
