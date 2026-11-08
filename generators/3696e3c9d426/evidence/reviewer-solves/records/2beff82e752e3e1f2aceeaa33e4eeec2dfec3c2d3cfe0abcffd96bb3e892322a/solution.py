def solve(grid):
    """Apply downward gravity independently in every column."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    for column in range(width):
        cells = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        first_row = height - len(cells)
        for offset, color in enumerate(cells):
            output[first_row + offset][column] = color

    return output
