def solve(grid):
    """Overlay the two four-row panels by nonzero occupancy."""
    if not isinstance(grid, list) or len(grid) != 9 or not grid[0]:
        raise ValueError("expected a nonempty 9-row grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    return [
        [3 if grid[row][col] != 0 or grid[row + 5][col] != 0 else 0
         for col in range(width)]
        for row in range(4)
    ]
