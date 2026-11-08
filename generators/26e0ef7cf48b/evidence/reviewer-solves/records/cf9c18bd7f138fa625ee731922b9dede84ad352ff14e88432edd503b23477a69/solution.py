def solve(grid):
    """Stamp the color-2 pattern at every color-3 or color-4 anchor."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    template_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if not template_cells:
        return [[0 for _ in range(width)] for _ in range(height)]

    top = min(row for row, _ in template_cells)
    left = min(col for _, col in template_cells)
    offsets = [(row - top, col - left) for row, col in template_cells]

    output = [[0 for _ in range(width)] for _ in range(height)]
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (3, 4)
    ]

    for anchor_row, anchor_col in anchors:
        for row_offset, col_offset in offsets:
            row = anchor_row + row_offset
            col = anchor_col + col_offset
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = 8

    # Color 9 is a hole: it remains blank even when a stamp overlaps it.
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 9:
                output[row][col] = 0

    return output
