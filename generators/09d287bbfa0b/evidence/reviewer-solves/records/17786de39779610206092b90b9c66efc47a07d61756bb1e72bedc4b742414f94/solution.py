def solve(grid):
    """Mirror every off-axis colored source through the full row/column cross."""
    height = len(grid)
    width = len(grid[0])

    # The examples contain one complete monochrome non-7 row and column.  Their
    # intersection is the center of the reflection cross.
    axis_row = next(
        row
        for row in range(height)
        if all(grid[row][col] != 7 for col in range(width))
        and len(set(grid[row])) == 1
    )
    axis_col = next(
        col
        for col in range(width)
        if all(grid[row][col] != 7 for row in range(height))
        and len({grid[row][col] for row in range(height)}) == 1
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
        for target_row in (row, 2 * axis_row - row):
            for target_col in (col, 2 * axis_col - col):
                if 0 <= target_row < height and 0 <= target_col < width:
                    result[target_row][target_col] = color
    return result
