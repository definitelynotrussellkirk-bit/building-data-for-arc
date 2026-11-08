def solve(grid):
    """Complete a hollow plus only when all four arms have one color."""
    result = [list(row) for row in grid]
    if not grid:
        return result
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] != 0:
                continue
            color = grid[r - 1][c]
            if (color != 0 and grid[r + 1][c] == color
                    and grid[r][c - 1] == color and grid[r][c + 1] == color):
                result[r][c] = color
    return result
