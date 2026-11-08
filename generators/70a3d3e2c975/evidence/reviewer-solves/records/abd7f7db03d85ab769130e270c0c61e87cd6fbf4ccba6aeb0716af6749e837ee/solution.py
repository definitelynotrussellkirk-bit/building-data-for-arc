def solve(grid):
    height, width = len(grid), len(grid[0])
    candidates = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    if len(candidates) != 1:
        raise ValueError("Expected one full column of 9s")
    axis = candidates[0]
    result = [list(row) for row in grid]
    for r in range(height):
        for c in range(axis):
            target = 2 * axis - c
            if grid[r][c] not in (0, 9) and 0 <= target < width:
                result[r][target] = grid[r][c]
    return result
