def solve(grid):
    """Sort the variable stripe-columns by their foreground population.

    The constant foreground columns and all-zero separator columns form a fixed
    frame.  Each remaining column is a binary stripe.  The output keeps the
    frame in place and stably orders those stripe columns from sparsest to
    densest.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    variable_columns = [
        column
        for column in range(width)
        if len({grid[row][column] for row in range(height)}) > 1
    ]
    ordered_sources = sorted(
        variable_columns,
        key=lambda column: sum(grid[row][column] != 0 for row in range(height)),
    )

    result = [row[:] for row in grid]
    for destination, source in zip(variable_columns, ordered_sources):
        for row in range(height):
            result[row][destination] = grid[row][source]
    return result
