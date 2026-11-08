def solve(grid):
    """Drop the header row/column and paint row/column header matches."""
    column_headers = grid[0][1:]
    row_headers = [row[0] for row in grid[1:]]
    return [
        [row_color if row_color == column_color else 0
         for column_color in column_headers]
        for row_color in row_headers
    ]
