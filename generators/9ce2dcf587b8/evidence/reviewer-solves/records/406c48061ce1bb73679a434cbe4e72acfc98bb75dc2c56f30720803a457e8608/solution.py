def solve(grid):
    """Extend every nonzero marker along all four diagonals to the boundary."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]

    for row, col, color in markers:
        for delta_row, delta_col in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            next_row = row + delta_row
            next_col = col + delta_col
            while 0 <= next_row < height and 0 <= next_col < width:
                # The visible examples use one marker color.  Keeping existing
                # nonzero cells intact is the least destructive extension if
                # two rays ever meet a source marker.
                if output[next_row][next_col] == 0:
                    output[next_row][next_col] = color
                next_row += delta_row
                next_col += delta_col

    return output
