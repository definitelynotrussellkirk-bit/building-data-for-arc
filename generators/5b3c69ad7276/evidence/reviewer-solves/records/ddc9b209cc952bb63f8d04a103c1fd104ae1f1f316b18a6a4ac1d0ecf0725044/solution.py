def solve(grid):
    """Fill the full row and column through the single nonzero cell."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    marker = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                marker = (r, c, value)
                break
        if marker is not None:
            break

    if marker is None:
        return out

    r0, c0, color = marker
    for c in range(width):
        out[r0][c] = color
    for r in range(height):
        out[r][c0] = color
    return out
