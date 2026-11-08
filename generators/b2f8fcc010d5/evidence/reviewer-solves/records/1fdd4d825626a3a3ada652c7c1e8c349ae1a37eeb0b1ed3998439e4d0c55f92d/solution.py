def solve(grid):
    """Untwist the checkerboard frame into a 3×3 grid."""
    last = len(grid) - 1
    mid = last // 2
    return [
        [grid[0][0], grid[1][1], grid[0][last]],
        [grid[1][last - 1], grid[mid][mid], grid[last - 1][1]],
        [grid[last][0], grid[last - 1][last - 1], grid[last][last]],
    ]
