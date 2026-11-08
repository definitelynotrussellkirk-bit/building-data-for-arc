def solve(grid):
    """Complete reflection about the axis marked by color 8."""
    height = len(grid)
    width = len(grid[0])
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if not markers:
        return [row[:] for row in grid]

    marker_columns = {col for _, col in markers}
    output = [row[:] for row in grid]
    if len(marker_columns) == 1:
        axis = next(iter(marker_columns))
        for row in range(height):
            for col in range(width):
                value = grid[row][col]
                target_col = 2 * axis - col
                if (
                    value not in (0, 8)
                    and 0 <= target_col < width
                    and output[row][target_col] == 0
                ):
                    output[row][target_col] = value
    else:
        axis = markers[0][0]
        for row in range(height):
            for col in range(width):
                value = grid[row][col]
                target_row = 2 * axis - row
                if (
                    value not in (0, 8)
                    and 0 <= target_row < height
                    and output[target_row][col] == 0
                ):
                    output[target_row][col] = value
    return output
