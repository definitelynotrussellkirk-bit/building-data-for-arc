def solve(grid):
    """Move the central marker according to the separator-panel containing color 6."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    separator_rows = [r for r in range(height) if all(value == 0 for value in grid[r])]
    separator_cols = [
        c for c in range(width) if all(grid[r][c] == 0 for r in range(height))
    ]

    sixes = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    nines = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(sixes) != 1 or len(nines) != 1 or len(separator_rows) != 2 or len(separator_cols) != 2:
        raise ValueError("expected one 6, one 9, and a 3-by-3 separator layout")

    six_r, six_c = sixes[0]
    center_r, center_c = nines[0]
    panel_r = sum(separator < six_r for separator in separator_rows)
    panel_c = sum(separator < six_c for separator in separator_cols)

    target_r = center_r + panel_r - 1
    target_c = center_c + panel_c - 1

    out[center_r][center_c] = 5
    out[target_r][target_c] = 9
    out[six_r][six_c] = 9
    return out
