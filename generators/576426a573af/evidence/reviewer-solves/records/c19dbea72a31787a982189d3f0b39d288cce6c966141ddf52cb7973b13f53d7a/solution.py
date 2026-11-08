def solve(grid):
    """Complete horizontal mirror pairs without overwriting given colors."""
    original = [row[:] for row in grid]
    result = [row[:] for row in grid]
    height = len(original)

    for row_index, row in enumerate(original):
        mirror_row = height - 1 - row_index
        for column_index, color in enumerate(row):
            if color != 0 and result[mirror_row][column_index] == 0:
                result[mirror_row][column_index] = color

    return result
