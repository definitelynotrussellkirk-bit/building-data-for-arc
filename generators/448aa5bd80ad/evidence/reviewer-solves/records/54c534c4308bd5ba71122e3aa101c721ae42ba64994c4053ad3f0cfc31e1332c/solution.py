def solve(grid):
    """Crop the colored object and orient it from marker/object overlap."""
    object_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not object_cells:
        return []

    r0 = min(r for r, _ in object_cells)
    r1 = max(r for r, _ in object_cells)
    c0 = min(c for _, c in object_cells)
    c1 = max(c for _, c in object_cells)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    marker_columns = {
        c
        for row in grid
        for c, value in enumerate(row)
        if value == 9
    }
    overlaps = sum(c0 <= c <= c1 for c in marker_columns)

    if overlaps == 1:
        # One projected marker: reflect across the main diagonal.
        return [list(row) for row in zip(*crop)]

    # Zero or two projected markers in the visible examples: turn the crop around.
    return [row[::-1] for row in crop[::-1]]
