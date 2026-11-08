def solve(grid):
    """Recolor each gray (8) cell from the nonzero header in its column."""
    if not grid:
        return []

    out = [row[:] for row in grid]
    header = grid[0]
    for r in range(1, len(grid)):
        for c, value in enumerate(grid[r]):
            if value == 8 and header[c] != 0:
                out[r][c] = header[c]
    return out
