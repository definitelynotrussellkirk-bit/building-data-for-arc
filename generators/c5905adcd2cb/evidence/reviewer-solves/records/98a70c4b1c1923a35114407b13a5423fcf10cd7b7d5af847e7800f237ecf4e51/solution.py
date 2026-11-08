def solve(grid):
    """Decode the marker-selected source and destination lattice cells."""
    height = len(grid)
    width = len(grid[0])

    marker = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    )
    marker_row, marker_col = marker
    source_row = (marker_row // 4) * 4
    source_col = (marker_col // 4) * 4
    local_row = marker_row - source_row
    local_col = marker_col - source_col
    destination_row = local_row * 4
    destination_col = local_col * 4

    source_cells = [
        (row - source_row, col - source_col, grid[row][col])
        for row in range(source_row, source_row + 3)
        for col in range(source_col, source_col + 3)
        if grid[row][col] not in (0, 5)
    ]

    output = [
        [5 if grid[row][col] == 5 else 0 for col in range(width)]
        for row in range(height)
    ]
    for row_offset, col_offset, value in source_cells:
        output[destination_row + row_offset][destination_col + col_offset] = value
    return output
