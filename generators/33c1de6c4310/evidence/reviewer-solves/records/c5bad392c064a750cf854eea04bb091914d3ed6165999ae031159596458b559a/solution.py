def solve(grid):
    """Use the left panel as a binary stencil over the right panel."""
    if not grid:
        return []

    width = len(grid[0])
    divider_columns = [
        column
        for column in range(width)
        if all(len(row) == width and row[column] == 9 for row in grid)
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected exactly one full-height color-9 divider")

    divider = divider_columns[0]
    panel_width = divider
    if width - divider - 1 != panel_width:
        raise ValueError("left and right panels must have equal widths")

    return [
        [right_value if mask_value != 0 else 0
         for mask_value, right_value in zip(row[:divider], row[divider + 1:])]
        for row in grid
    ]
