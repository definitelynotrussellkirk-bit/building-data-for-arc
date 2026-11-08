def solve(grid):
    """Construct the colored equality table described by the visible headers."""
    if len(grid) < 2 or len(grid[0]) < 2:
        raise ValueError("Expected a header row and a header column")
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a rectangular grid")
    column_headers = grid[0][1:]
    return [
        [row[0] if row[0] != 0 and row[0] == top else 0
         for top in column_headers]
        for row in grid[1:]
    ]
