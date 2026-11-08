def solve(grid):
    """Find the cross by occupancy, then color its surrounding ring yellow."""
    height, width = len(grid), len(grid[0])
    row = next(r for r in range(height) if all(grid[r][c] != 0 for c in range(width)))
    col = next(c for c in range(width) if all(grid[r][c] != 0 for r in range(height)))
    out = [list(line) for line in grid]
    for r in range(max(0, row - 1), min(height, row + 2)):
        for c in range(max(0, col - 1), min(width, col + 2)):
            if (r, c) != (row, col):
                out[r][c] = 4
    return out
