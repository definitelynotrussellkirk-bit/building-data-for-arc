def solve(grid):
    """Fill a zero lying exactly between equal nonzero cells in a row or column."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for r in range(height):
        for c in range(width - 2):
            color = grid[r][c]
            if color != 0 and grid[r][c + 1] == 0 and grid[r][c + 2] == color:
                out[r][c + 1] = color

    for r in range(height - 2):
        for c in range(width):
            color = grid[r][c]
            if color != 0 and grid[r + 1][c] == 0 and grid[r + 2][c] == color:
                out[r + 1][c] = color

    return out
