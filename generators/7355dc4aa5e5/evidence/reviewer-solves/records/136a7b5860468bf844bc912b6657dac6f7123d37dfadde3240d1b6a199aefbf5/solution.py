def solve(grid):
    """Expand every original blue marker into a colored cross-and-diagonals stamp."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    height = len(grid)
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    # Capture the markers before painting, since newly painted blue cells are not
    # additional centers.  The examples are consistent with row-major processing.
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    result = [row[:] for row in grid]

    for row, col in markers:
        for other_col in range(width):
            result[row][other_col] = 1
        for other_row in range(height):
            result[other_row][col] = 1
        result[row][col] = 2
        for row_delta, col_delta in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            target_row = row + row_delta
            target_col = col + col_delta
            if 0 <= target_row < height and 0 <= target_col < width:
                result[target_row][target_col] = 3

    return result
