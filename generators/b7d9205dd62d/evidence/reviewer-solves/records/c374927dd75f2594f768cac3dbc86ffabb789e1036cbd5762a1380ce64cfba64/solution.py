def solve(grid):
    """Fill rectangles indicated by diagonally separated same-color markers."""
    output = [row[:] for row in grid]
    positions = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    for color, cells in positions.items():
        min_row = min(row for row, column in cells)
        max_row = max(row for row, column in cells)
        min_column = min(column for row, column in cells)
        max_column = max(column for row, column in cells)
        if min_row < max_row and min_column < max_column:
            for row in range(min_row, max_row + 1):
                for column in range(min_column, max_column + 1):
                    output[row][column] = color
    return output
