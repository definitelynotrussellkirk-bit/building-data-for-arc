def solve(grid):
    """Crop to the non-background bounding box, then rotate it 90° clockwise."""
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

    cropped = [row[left : right + 1] for row in grid[top : bottom + 1]]
    return [list(column) for column in zip(*cropped[::-1])]
