def solve(grid):
    """Mark the empty cell immediately southwest of each maroon cell."""
    output = [list(row) for row in grid]
    height = len(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 9:
                continue
            target_row, target_col = row + 1, col - 1
            if (target_row < height and target_col >= 0
                    and target_col < len(grid[target_row])
                    and grid[target_row][target_col] == 0):
                output[target_row][target_col] = 5
    return output
