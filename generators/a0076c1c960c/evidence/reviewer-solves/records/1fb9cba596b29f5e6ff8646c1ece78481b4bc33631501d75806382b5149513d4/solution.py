def solve(grid):
    """Replace each horizontal marker pair by cyan cells strictly between it."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0] * width for _ in range(height)]

    for row_index, row in enumerate(grid):
        marker_columns = [column for column, value in enumerate(row) if value != 0]
        if len(marker_columns) == 2:
            left, right = marker_columns
            for column in range(left + 1, right):
                output[row_index][column] = 8

    return output
