def solve(grid):
    """Keep the grid and add each nonzero cell's main-diagonal reflection."""
    size = len(grid)
    out = [row[:] for row in grid]
    for row in range(size):
        for col in range(size):
            color = grid[row][col]
            if color != 0 and out[col][row] == 0:
                out[col][row] = color
    return out
