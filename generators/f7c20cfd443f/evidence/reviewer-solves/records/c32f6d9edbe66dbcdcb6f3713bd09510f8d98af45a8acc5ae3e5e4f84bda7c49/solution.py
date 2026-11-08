def solve(grid):
    """Replace every gray marker (5) by a clipped 3x3 blue block (1)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0 for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue
            for out_row in range(max(0, row - 1), min(height, row + 2)):
                for out_col in range(max(0, col - 1), min(width, col + 2)):
                    result[out_row][out_col] = 1

    return result
