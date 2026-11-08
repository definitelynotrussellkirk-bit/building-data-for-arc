def solve(grid):
    """Undo a non-uniform nearest-neighbour enlargement of a small grid."""
    if not grid or not grid[0]:
        return []

    # Each output row was enlarged to one or more identical adjacent rows.
    row_starts = [0]
    for row_index in range(1, len(grid)):
        if grid[row_index] != grid[row_index - 1]:
            row_starts.append(row_index)

    # Each output column was likewise enlarged. Compare full column vectors so
    # equal colours in neighbouring cells do not create a false boundary.
    column_starts = [0]
    width = len(grid[0])
    for column_index in range(1, width):
        previous = tuple(row[column_index - 1] for row in grid)
        current = tuple(row[column_index] for row in grid)
        if current != previous:
            column_starts.append(column_index)

    return [
        [grid[row_index][column_index] for column_index in column_starts]
        for row_index in row_starts
    ]
