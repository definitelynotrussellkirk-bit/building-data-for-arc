def solve(grid):
    """Pack every column upward, preserving the order of nonzero cells."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for col in range(width):
        packed = [grid[row][col] for row in range(height) if grid[row][col] != 0]
        for row, value in enumerate(packed):
            out[row][col] = value
    return out
