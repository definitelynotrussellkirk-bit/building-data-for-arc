def solve(grid):
    """Pack each nonzero column downward, preserving top-to-bottom order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        start = height - len(values)
        for offset, value in enumerate(values):
            out[start + offset][column] = value
    return out
