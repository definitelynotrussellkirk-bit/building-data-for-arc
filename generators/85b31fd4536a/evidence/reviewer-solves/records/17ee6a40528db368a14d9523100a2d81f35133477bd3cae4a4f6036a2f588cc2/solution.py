def solve(grid):
    """Apply the binary mask left of the 9-column to the colored grid at right."""
    if not grid:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separator_cols = [
        c for c in range(width)
        if all(row[c] == 9 for row in grid)
    ]
    if len(separator_cols) != 1:
        raise ValueError("expected exactly one full-height separator column of 9s")

    sep = separator_cols[0]
    mask_width = sep
    values_width = width - sep - 1
    if mask_width != values_width:
        raise ValueError("mask and value regions must have equal width")

    return [
        [value if mask else 0 for mask, value in zip(row[:sep], row[sep + 1:])]
        for row in grid
    ]
