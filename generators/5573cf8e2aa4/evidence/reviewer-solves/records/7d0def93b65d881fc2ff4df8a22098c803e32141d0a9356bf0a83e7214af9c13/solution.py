def solve(grid):
    """Overlay the two panels; mark their nonzero union in cyan (8)."""
    if not grid or len(grid[0]) % 2 != 1:
        raise ValueError("Expected two equal panels with one separator column")
    width = (len(grid[0]) - 1) // 2
    if any(len(row) != 2 * width + 1 for row in grid):
        raise ValueError("Expected a rectangular grid")
    return [
        [8 if row[c] != 0 or row[width + 1 + c] != 0 else 0
         for c in range(width)]
        for row in grid
    ]
