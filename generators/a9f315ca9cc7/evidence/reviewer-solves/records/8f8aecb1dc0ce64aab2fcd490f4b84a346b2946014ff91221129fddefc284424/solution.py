def solve(grid):
    """Replace every nonzero input cell by a copy of the whole input grid."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width * width)] for _ in range(height * height)]

    for block_row in range(height):
        for block_col in range(width):
            if grid[block_row][block_col] == 0:
                continue
            for row in range(height):
                for col in range(width):
                    output[block_row * height + row][block_col * width + col] = grid[row][col]
    return output
