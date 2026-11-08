def solve(grid):
    """Overlay the two panels and color their occupied intersection azure."""
    height = len(grid)
    divider = next(
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 9 for row in range(height))
    )
    right_start = divider + 1
    return [
        [8 if row[col] != 0 and row[right_start + col] != 0 else 0
         for col in range(divider)]
        for row in grid
    ]
