def solve(grid):
    """Reflect colored cells across the full-height cyan divider."""
    height, width = len(grid), len(grid[0])
    dividers = [c for c in range(width) if all(grid[r][c] == 8 for r in range(height))]
    if len(dividers) != 1:
        raise ValueError("Expected one full-height cyan divider")
    axis = dividers[0]
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            reflected = 2 * axis - c
            if color not in (0, 8) and 0 <= reflected < width:
                if result[r][reflected] == 0:
                    result[r][reflected] = color
    return result
