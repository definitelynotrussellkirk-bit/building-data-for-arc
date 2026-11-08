def solve(grid):
    """Crop the non-marker object and enlarge every cell by the marker count."""
    scale = sum(cell == 1 for row in grid for cell in row)
    if scale <= 0:
        raise ValueError("expected at least one scale marker of color 1")

    object_cells = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, cell in enumerate(row)
        if cell not in (0, 1)
    ]
    if not object_cells:
        raise ValueError("expected a non-background object distinct from color 1")

    top = min(row for row, _ in object_cells)
    bottom = max(row for row, _ in object_cells)
    left = min(column for _, column in object_cells)
    right = max(column for _, column in object_cells)

    cropped = [row[left : right + 1] for row in grid[top : bottom + 1]]
    enlarged = []
    for row in cropped:
        expanded_row = [cell for cell in row for _ in range(scale)]
        enlarged.extend([expanded_row.copy() for _ in range(scale)])
    return enlarged
