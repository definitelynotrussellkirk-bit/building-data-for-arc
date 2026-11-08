def solve(grid):
    """Replace every color-1 marker with a centered copy of the 3x3 key."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    # The visible examples place the key in the upper-left 3x3 block, to the
    # left of the solid separator column.  Capture markers before painting so
    # overlapping copies cannot create or erase work-list entries.
    key = [row[:3] for row in grid[:3]]
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]

    for center_row, center_col in markers:
        for key_row in range(3):
            for key_col in range(3):
                out_row = center_row + key_row - 1
                out_col = center_col + key_col - 1
                if 0 <= out_row < height and 0 <= out_col < width:
                    result[out_row][out_col] = key[key_row][key_col]

    return result
