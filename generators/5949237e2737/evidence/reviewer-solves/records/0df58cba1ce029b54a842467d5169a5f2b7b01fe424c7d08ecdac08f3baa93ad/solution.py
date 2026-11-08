def solve(grid):
    """Keep right-side cells that exactly match their mirror across the divider."""
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    # The demonstrations contain one solid non-background vertical separator.
    separators = [
        col
        for col in range(width)
        if grid[0][col] != 0 and all(grid[row][col] == grid[0][col] for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected one solid nonzero divider column, found {separators}")
    divider = separators[0]

    out = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(divider + 1, width):
            mirror_col = 2 * divider - col
            if mirror_col >= 0 and grid[row][col] != 0 and grid[row][col] == grid[row][mirror_col]:
                out[row][col] = grid[row][col]
    return out
