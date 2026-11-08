def solve(grid):
    """Compress the border/interior regions to 3x3, keeping the last nonzero."""
    height = len(grid)
    width = len(grid[0])
    result = [[0, 0, 0] for _ in range(3)]

    for row, values in enumerate(grid):
        out_row = 0 if row == 0 else 2 if row == height - 1 else 1
        for col, value in enumerate(values):
            if value == 0:
                continue
            out_col = 0 if col == 0 else 2 if col == width - 1 else 1
            result[out_row][out_col] = value

    return result
