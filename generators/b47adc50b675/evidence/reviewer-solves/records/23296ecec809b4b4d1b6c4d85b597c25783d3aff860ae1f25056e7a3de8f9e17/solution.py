def solve(grid):
    """Translate the nonzero figure so its bounding box begins at (0, 0)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    occupied = [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        return output

    top = min(row for row, _, _ in occupied)
    left = min(column for _, column, _ in occupied)
    for row, column, value in occupied:
        output[row - top][column - left] = value
    return output
