def solve(grid):
    """Pack each column's nonzero cells upward without reordering them."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        for row, value in enumerate(values):
            out[row][column] = value
    return out
