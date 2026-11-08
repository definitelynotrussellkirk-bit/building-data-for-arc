def solve(grid):
    """Crop to all nonzero cells, then rotate the crop 90 degrees clockwise."""
    cells = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []

    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(column for _, column in cells)
    right = max(column for _, column in cells)
    crop = [list(row[left : right + 1]) for row in grid[top : bottom + 1]]
    return [list(row) for row in zip(*crop[::-1])]
