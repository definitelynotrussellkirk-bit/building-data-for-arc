def solve(grid):
    """Mirror every off-axis colored source through the full row/column cross."""
    height = len(grid)
    width = len(grid[0])

    # The axes are the first row and column with no background-7 cells.  They
    # need not be monochrome: an example contains a differently colored cell
    # on the full row, which remains part of the inert axis.
    axis_row = next(
        row for row in range(height)
        if all(grid[row][col] != 7 for col in range(width))
    )
    axis_col = next(
        col for col in range(width)
        if all(grid[row][col] != 7 for row in range(height))
    )

    result = [row[:] for row in grid]
    sources = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if row != axis_row and col != axis_col and grid[row][col] != 7
    ]

    # Preserve the visible row-major overwrite behavior when reflected copies
    # collide.  Each target is clipped independently at the grid boundary.
    for row, col, color in sources:
        for target_row, target_col in (
            (2 * axis_row - row, col),
            (row, 2 * axis_col - col),
            (2 * axis_row - row, 2 * axis_col - col),
        ):
            if 0 <= target_row < height and 0 <= target_col < width:
                result[target_row][target_col] = color
    return result
