def solve(grid):
    """Crop the color-1 mask and tile recolored copies in row-0 palette order."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    palette = [value for value in grid[0] if value != 0]
    mask = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == 1
    ]
    if not palette or not mask:
        raise ValueError("expected a row-0 palette and a color-1 mask")

    top = min(row for row, _ in mask)
    bottom = max(row for row, _ in mask)
    left = min(column for _, column in mask)
    right = max(column for _, column in mask)
    height = bottom - top + 1
    width = right - left + 1
    normalized = {(row - top, column - left) for row, column in mask}

    output_width = len(palette) * width + len(palette) - 1
    output = [[0 for _ in range(output_width)] for _ in range(height)]
    for copy_index, color in enumerate(palette):
        offset = copy_index * (width + 1)
        for row, column in normalized:
            output[row][offset + column] = color
    return output
