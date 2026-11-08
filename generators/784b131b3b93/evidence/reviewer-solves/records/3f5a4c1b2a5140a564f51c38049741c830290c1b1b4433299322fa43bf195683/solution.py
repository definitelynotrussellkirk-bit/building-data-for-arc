def solve(grid):
    """Compare aligned cells in the two equal-width input halves."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    width = len(grid[0])
    if width % 2:
        raise ValueError("input width must be even")
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    half = width // 2
    return [
        [5 if row[c] == 0 and row[half + c] == 0 else 0 for c in range(half)]
        for row in grid
    ]
