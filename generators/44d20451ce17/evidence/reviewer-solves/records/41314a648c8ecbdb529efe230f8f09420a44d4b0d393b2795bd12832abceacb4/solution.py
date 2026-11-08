def solve(grid):
    """Collapse every column containing color 1 to one marker on the last row."""
    if not grid:
        return []
    width = len(grid[0])
    marked_columns = {
        c
        for row in grid
        for c, value in enumerate(row)
        if value == 1
    }
    out = [
        [0 if value == 1 else value for value in row]
        for row in grid
    ]
    for c in marked_columns:
        if c < width:
            out[-1][c] = 1
    return out
