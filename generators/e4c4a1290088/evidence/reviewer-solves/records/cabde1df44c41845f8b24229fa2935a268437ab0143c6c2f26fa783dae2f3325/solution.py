def solve(grid):
    """Fill an interior cell with its column header when both headers match."""
    output = [row[:] for row in grid]
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            output[r][c] = grid[0][c] if grid[r][0] == grid[0][c] else 0
    return output
