def solve(grid):
    """Overlay the two panels separated by the full-width middle row."""
    panel_height = len(grid) // 2
    top = grid[:panel_height]
    bottom = grid[panel_height + 1 :]
    return [
        [3 if top_value != 0 or bottom_value != 0 else 0
         for top_value, bottom_value in zip(top_row, bottom_row)]
        for top_row, bottom_row in zip(top, bottom)
    ]
