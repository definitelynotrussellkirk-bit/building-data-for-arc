def solve(grid):
    """Compare aligned zero/nonzero occupancy in the upper and lower panels."""
    half = len(grid) // 2
    return [
        [6 if (upper != 0) != (lower != 0) else 0
         for upper, lower in zip(grid[r], grid[r + half])]
        for r in range(half)
    ]
