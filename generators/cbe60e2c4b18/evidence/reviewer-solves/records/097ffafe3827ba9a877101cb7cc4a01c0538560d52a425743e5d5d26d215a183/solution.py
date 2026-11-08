def solve(grid):
    """Return the occupied-cell intersection of the two divider-separated panels."""
    separator = next(
        column
        for column in range(len(grid[0]))
        if all(row[column] == 9 for row in grid)
    )
    panel_width = separator
    return [
        [
            8 if row[column] != 0 and row[separator + 1 + column] != 0 else 0
            for column in range(panel_width)
        ]
        for row in grid
    ]
