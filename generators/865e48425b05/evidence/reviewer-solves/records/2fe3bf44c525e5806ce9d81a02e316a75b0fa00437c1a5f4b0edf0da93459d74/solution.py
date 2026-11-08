def solve(grid):
    """Crop the 1-mask and render one colored copy per singleton marker."""
    ones = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 1
    ]
    if not ones:
        return []

    top = min(row for row, _ in ones)
    bottom = max(row for row, _ in ones)
    left = min(col for _, col in ones)
    right = max(col for _, col in ones)

    markers = sorted(
        (
            (col_index, row_index, value)
            for row_index, row in enumerate(grid)
            for col_index, value in enumerate(row)
            if value not in (0, 1)
        )
    )
    colors = [value for _, _, value in markers]

    mask_height = bottom - top + 1
    mask_width = right - left + 1
    output_width = len(colors) * mask_width + max(0, len(colors) - 1)
    output = [[0 for _ in range(output_width)] for _ in range(mask_height)]

    for copy_index, color in enumerate(colors):
        offset = copy_index * (mask_width + 1)
        for row_index, col_index in ones:
            output[row_index - top][offset + col_index - left] = color

    return output
