def solve(grid):
    """Decode interior markers using the row and column color headers.

    The first column is the row key and the first row is the column key:
    marker 1 selects its row key, marker 2 selects its column key.  Header
    cells and every other interior value are preserved.
    """
    if not grid:
        return []

    out = [row[:] for row in grid]
    for row_index in range(1, len(grid)):
        for column_index in range(1, len(grid[row_index])):
            marker = grid[row_index][column_index]
            if marker == 1:
                out[row_index][column_index] = grid[row_index][0]
            elif marker == 2:
                out[row_index][column_index] = grid[0][column_index]
    return out
