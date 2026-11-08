def solve(grid):
    """Mirror only color-2 cells across the central column, recoloring copies 7."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    width = len(grid[0])
    axis = width // 2
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c in range(axis):
            if row[c] == 2:
                out[r][2 * axis - c] = 7
    return out
