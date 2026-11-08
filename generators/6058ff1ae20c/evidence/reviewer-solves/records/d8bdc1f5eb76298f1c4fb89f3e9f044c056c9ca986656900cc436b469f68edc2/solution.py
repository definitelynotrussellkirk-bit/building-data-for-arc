def solve(grid):
    """Expand every non-zero seed into its full row and column.

    Seeds are read in row-major order.  Applying them in that order reproduces
    the visible distinct-color example, where the lower/later seed owns the two
    cross intersections.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    for row, col, value in seeds:
        for target_row in range(height):
            output[target_row][col] = value
        for target_col in range(width):
            output[row][target_col] = value
    return output
