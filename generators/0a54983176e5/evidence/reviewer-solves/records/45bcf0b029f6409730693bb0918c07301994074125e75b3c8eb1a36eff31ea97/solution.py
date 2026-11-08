def solve(grid):
    """Complete a partial mirror image around the line marked by color 8.

    The 8-cells lie on one horizontal or vertical axis.  Every other colored
    cell is reflected once across that axis when the reflected coordinate is
    inside the grid and currently background; existing cells are preserved.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]

    if len(markers) < 2:
        return result

    marker_rows = {row for row, _ in markers}
    marker_cols = {col for _, col in markers}

    if len(marker_rows) == 1:
        axis = next(iter(marker_rows))
        for row in range(height):
            for col in range(width):
                color = grid[row][col]
                if color in (0, 8):
                    continue
                reflected_row = 2 * axis - row
                if 0 <= reflected_row < height and result[reflected_row][col] == 0:
                    result[reflected_row][col] = color
    elif len(marker_cols) == 1:
        axis = next(iter(marker_cols))
        for row in range(height):
            for col in range(width):
                color = grid[row][col]
                if color in (0, 8):
                    continue
                reflected_col = 2 * axis - col
                if 0 <= reflected_col < width and result[row][reflected_col] == 0:
                    result[row][reflected_col] = color

    return result
