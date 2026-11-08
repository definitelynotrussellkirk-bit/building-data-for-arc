"""Infer the magenta bounding rectangle from visible examples."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    canvas = [[0] * width for _ in range(height)]
    min_row, min_col = height, width
    max_row, max_col = -1, -1
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 6:
                min_row = min(min_row, row)
                min_col = min(min_col, col)
                max_row = max(max_row, row)
                max_col = max(max_col, col)
    if max_row < 0:
        return canvas
    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            canvas[row][col] = 6
    return canvas
