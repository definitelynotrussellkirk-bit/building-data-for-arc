def solve(grid):
    """Connect aligned equal-colored markers; lower colors win crossings."""
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    colors = sorted({value for row in grid for value in row if value != 0}, reverse=True)
    for color in colors:
        positions = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]

        by_row = {}
        by_col = {}
        for r, c in positions:
            by_row.setdefault(r, []).append(c)
            by_col.setdefault(c, []).append(r)

        for r, cols in by_row.items():
            if len(cols) >= 2:
                for c in range(min(cols), max(cols) + 1):
                    out[r][c] = color

        for c, rows in by_col.items():
            if len(rows) >= 2:
                for r in range(min(rows), max(rows) + 1):
                    out[r][c] = color

    return out
