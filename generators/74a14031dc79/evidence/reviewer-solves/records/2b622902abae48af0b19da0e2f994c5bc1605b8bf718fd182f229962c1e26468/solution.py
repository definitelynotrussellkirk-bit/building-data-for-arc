def solve(grid):
    """Overlay the two equal-width panels separated by the middle column."""
    width = len(grid[0])
    divider = width // 2
    panel_width = divider
    return [
        [
            2 if row[col] != 0 or row[divider + 1 + col] != 0 else 0
            for col in range(panel_width)
        ]
        for row in grid
    ]
