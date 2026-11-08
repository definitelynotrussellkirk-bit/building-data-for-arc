def solve(grid):
    """Add a gray shadow one step down-left of each maroon cell.

    The original grid is preserved.  A shadow is painted only when its target
    lies inside the grid and is background, so existing colored cells win.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 9:
                continue
            target_row = row + 1
            target_col = col - 1
            if (
                0 <= target_row < height
                and 0 <= target_col < width
                and out[target_row][target_col] == 0
            ):
                out[target_row][target_col] = 5

    return out
