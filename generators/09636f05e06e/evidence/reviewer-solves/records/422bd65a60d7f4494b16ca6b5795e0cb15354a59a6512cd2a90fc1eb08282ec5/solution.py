def solve(grid):
    """Clear rows and columns selected by input zeros, preserving color 2."""
    zero_rows = set()
    zero_columns = set()
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 0:
                zero_rows.add(row_index)
                zero_columns.add(column_index)
    return [
        [
            0 if value != 2 and (row_index in zero_rows or column_index in zero_columns) else value
            for column_index, value in enumerate(row)
        ]
        for row_index, row in enumerate(grid)
    ]
