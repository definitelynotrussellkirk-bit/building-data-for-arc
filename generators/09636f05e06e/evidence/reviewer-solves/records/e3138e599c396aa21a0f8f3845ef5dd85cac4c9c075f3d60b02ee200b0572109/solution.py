def solve(grid):
    """Erase every row/column containing a zero, while preserving color 2."""
    zero_rows = {
        row_index
        for row_index, row in enumerate(grid)
        if any(cell == 0 for cell in row)
    }
    zero_columns = {
        column_index
        for row in grid
        for column_index, cell in enumerate(row)
        if cell == 0
    }

    return [
        [
            cell
            if cell == 2 or (row_index not in zero_rows and column_index not in zero_columns)
            else 0
            for column_index, cell in enumerate(row)
        ]
        for row_index, row in enumerate(grid)
    ]
