def solve(grid):
    """Color the five zones of the cross formed by two cyan dividers."""
    if not grid or not grid[0]:
        return []

    height, width = len(grid), len(grid[0])
    divider_rows = [r for r, row in enumerate(grid) if all(value == 8 for value in row)]
    divider_cols = [
        c for c in range(width)
        if all(grid[r][c] == 8 for r in range(height))
    ]
    if len(divider_rows) != 2 or len(divider_cols) != 2:
        raise ValueError("expected exactly two complete cyan rows and columns")

    r0, r1 = divider_rows
    c0, c1 = divider_cols
    row_bands = (range(0, r0), range(r0 + 1, r1), range(r1 + 1, height))
    col_bands = (range(0, c0), range(c0 + 1, c1), range(c1 + 1, width))

    output = [row[:] for row in grid]
    zone_colors = {
        (0, 1): 2,
        (1, 0): 4,
        (1, 1): 6,
        (1, 2): 3,
        (2, 1): 1,
    }
    for (row_zone, col_zone), color in zone_colors.items():
        for r in row_bands[row_zone]:
            for c in col_bands[col_zone]:
                output[r][c] = color
    return output
