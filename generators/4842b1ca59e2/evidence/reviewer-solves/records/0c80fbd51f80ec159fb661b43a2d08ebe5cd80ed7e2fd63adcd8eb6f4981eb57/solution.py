def solve(grid):
    """Fill each nonempty column with its topmost nonzero color."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    height = len(grid)
    result = [[0 for _ in range(width)] for _ in range(height)]
    for col in range(width):
        color = next((grid[row][col] for row in range(height) if grid[row][col] != 0), 0)
        if color:
            for row in range(height):
                result[row][col] = color
    return result
