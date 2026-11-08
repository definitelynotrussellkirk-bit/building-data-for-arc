def solve(grid):
    """Crop to the bounding rectangle containing every color-6 cell."""
    rows = []
    cols = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 6:
                rows.append(r)
                cols.append(c)

    if not rows:
        # The visible task always contains color 6.  Returning a copy keeps the
        # function total without inventing a crop for an unsupported input.
        return [list(row) for row in grid]

    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]
