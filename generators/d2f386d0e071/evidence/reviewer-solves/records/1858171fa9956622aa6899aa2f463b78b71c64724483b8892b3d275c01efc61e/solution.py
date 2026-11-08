def solve(grid):
    """Reflect every colored cell across the grid's vertical midline."""
    out = [row[:] for row in grid]
    width = len(grid[0]) if grid else 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                out[r][width - 1 - c] = value
    return out
