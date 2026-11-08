def solve(grid):
    """Reflect the populated side across the full-height colored separator."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    separators = [
        c
        for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected one full-height nonzero separator, found {separators}")

    axis = separators[0]
    left_count = sum(grid[r][c] != 0 for r in range(height) for c in range(axis))
    right_count = sum(grid[r][c] != 0 for r in range(height) for c in range(axis + 1, width))

    if left_count >= right_count:
        for r in range(height):
            for c in range(axis):
                mirror = 2 * axis - c
                if mirror < width:
                    out[r][mirror] = grid[r][c]
    else:
        for r in range(height):
            for c in range(axis + 1, width):
                mirror = 2 * axis - c
                if mirror >= 0:
                    out[r][mirror] = grid[r][c]
    return out
