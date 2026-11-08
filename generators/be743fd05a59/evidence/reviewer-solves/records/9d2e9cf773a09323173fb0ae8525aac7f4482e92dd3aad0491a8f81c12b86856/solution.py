def solve(grid):
    """Copy the grid and mark the empty cell diagonally down-left of each 9."""
    out = [row[:] for row in grid]
    height = len(grid)

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 9:
                continue

            target_row = row_index + 1
            target_col = col_index - 1
            if (
                0 <= target_row < height
                and 0 <= target_col < len(grid[target_row])
                and grid[target_row][target_col] == 0
            ):
                out[target_row][target_col] = 5

    return out
