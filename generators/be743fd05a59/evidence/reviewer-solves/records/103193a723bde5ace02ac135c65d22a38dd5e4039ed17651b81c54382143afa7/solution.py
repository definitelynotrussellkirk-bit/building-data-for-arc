def solve(grid):
    """Add a 5 one cell down-left of every 9 when that cell is empty."""
    out = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value != 9:
                continue
            target_row = row_index + 1
            target_column = column_index - 1
            if (
                0 <= target_row < len(out)
                and 0 <= target_column < len(out[target_row])
                and out[target_row][target_column] == 0
            ):
                out[target_row][target_column] = 5
    return out
