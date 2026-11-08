def solve(grid):
    """Outline green blocks, using the unchanged input to identify boundaries."""
    result = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for column in range(width):
            if grid[row][column] != 3:
                continue
            neighbors = ((row - 1, column), (row + 1, column),
                         (row, column - 1), (row, column + 1))
            interior = all(
                0 <= r < height and 0 <= c < width and grid[r][c] == 3
                for r, c in neighbors
            )
            if not interior:
                result[row][column] = 8
    return result
