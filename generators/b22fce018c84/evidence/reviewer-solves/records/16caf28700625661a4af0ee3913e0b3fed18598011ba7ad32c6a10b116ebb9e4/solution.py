def solve(grid):
    """Preserve every cell and add each orange marker's horizontal reflection."""
    out = [row[:] for row in grid]
    height = len(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 7:
                out[height - 1 - row][col] = 7
    return out
