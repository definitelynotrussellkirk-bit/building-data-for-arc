def solve(grid):
    """Fill each marked column's inclusive vertical span with color 8."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    result = [[0] * width for _ in range(height)]
    for column in range(width):
        marked_rows = [row for row in range(height) if grid[row][column] != 0]
        if marked_rows:
            for row in range(min(marked_rows), max(marked_rows) + 1):
                result[row][column] = 8
    return result
