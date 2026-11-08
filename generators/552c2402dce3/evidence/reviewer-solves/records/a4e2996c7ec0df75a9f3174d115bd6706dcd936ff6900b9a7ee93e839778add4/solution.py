def solve(grid):
    """Complete every almost-filled 2x2 monochrome block in one pass."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    for row in range(height - 1):
        for col in range(width - 1):
            cells = [
                grid[row][col],
                grid[row][col + 1],
                grid[row + 1][col],
                grid[row + 1][col + 1],
            ]
            nonzero = [value for value in cells if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                missing = cells.index(0)
                dr, dc = divmod(missing, 2)
                result[row + dr][col + dc] = nonzero[0]

    return result
