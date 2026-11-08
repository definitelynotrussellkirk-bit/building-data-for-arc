def solve(grid):
    """Replace each zero with its zero-containing column's left-to-right rank."""
    zero_columns = sorted(
        {column for row in grid for column, value in enumerate(row) if value == 0}
    )
    rank = {column: index + 1 for index, column in enumerate(zero_columns)}
    return [
        [rank[column] if value == 0 else value for column, value in enumerate(row)]
        for row in grid
    ]
