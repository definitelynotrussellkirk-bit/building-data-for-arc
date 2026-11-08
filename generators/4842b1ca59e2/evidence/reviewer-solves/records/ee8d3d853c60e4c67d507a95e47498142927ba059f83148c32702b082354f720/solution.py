def solve(grid):
    """Fill each occupied column with its topmost non-zero color."""
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    column_colors = []
    for col in range(width):
        color = 0
        for row in range(len(grid)):
            value = grid[row][col]
            if value != 0:
                color = value
                break
        column_colors.append(color)

    return [column_colors[:] for _ in grid]
