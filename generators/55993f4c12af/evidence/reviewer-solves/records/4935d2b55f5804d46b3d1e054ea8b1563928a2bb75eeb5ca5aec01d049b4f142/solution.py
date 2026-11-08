def solve(grid):
    """Overlay equal top/bottom panels and mark their occupancy union yellow."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if len(grid) % 2:
        raise ValueError("input height must split into two equal panels")
    half = len(grid) // 2
    return [
        [4 if grid[row][col] != 0 or grid[half + row][col] != 0 else 0
         for col in range(width)]
        for row in range(half)
    ]
