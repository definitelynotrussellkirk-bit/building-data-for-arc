def solve(grid):
    """Replace each zero by the left-to-right rank of its occupied column."""
    zero_columns = sorted(
        {column for row in grid for column, value in enumerate(row) if value == 0}
    )
    color_for_column = {
        column: rank for rank, column in enumerate(zero_columns, start=1)
    }
    return [
        [color_for_column[column] if value == 0 else value
         for column, value in enumerate(row)]
        for row in grid
    ]
