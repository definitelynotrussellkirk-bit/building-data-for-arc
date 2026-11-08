def solve(grid):
    """Paint the outer frame with the unique nonzero input color."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    colors = [value for row in grid for value in row if value != 0]
    if len(colors) != 1:
        raise ValueError("expected exactly one nonzero cell")
    color = colors[0]
    height = len(grid)
    return [
        [
            color if row in (0, height - 1) or column in (0, width - 1) else 0
            for column in range(width)
        ]
        for row in range(height)
    ]
