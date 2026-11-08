def solve(grid):
    """Add the main-diagonal reflection of every nonzero cell."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if height != width:
        raise ValueError("the visible task uses square grids")

    result = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value != 0:
                result[col][row] = value
    return result
