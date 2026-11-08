def solve(grid):
    """Expand every column containing exactly one nonzero cell.

    The unique nonzero color is copied down the full column; all other
    columns become background (0).
    """
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    column_colors = []
    for col in range(width):
        nonzero = [grid[row][col] for row in range(height) if grid[row][col] != 0]
        column_colors.append(nonzero[0] if len(nonzero) == 1 else 0)
    return [column_colors[:] for _ in range(height)]
