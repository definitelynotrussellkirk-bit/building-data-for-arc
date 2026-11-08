def solve(grid):
    """Keep the endpoints of each vertical run of one nonzero color."""
    height = len(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if (color != 0 and 0 < r < height - 1
                    and grid[r - 1][c] == color
                    and grid[r + 1][c] == color):
                out[r][c] = 0
    return out
