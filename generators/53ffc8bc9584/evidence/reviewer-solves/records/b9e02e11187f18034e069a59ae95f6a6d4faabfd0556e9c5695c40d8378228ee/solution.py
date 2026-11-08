def solve(grid):
    """Complete yellow 2x2 corners, using the original input for every match."""
    result = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height - 1):
        for col in range(width - 1):
            cells = [(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)]
            if sum(grid[r][c] == 4 for r, c in cells) == 3:
                for r, c in cells:
                    if grid[r][c] == 0:
                        result[r][c] = 9
    return result
