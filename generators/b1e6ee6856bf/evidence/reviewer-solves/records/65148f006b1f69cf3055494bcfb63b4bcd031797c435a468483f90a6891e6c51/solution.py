def solve(grid):
    """Keep the first nonzero cell in each column and erase later ones."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(width):
        for row in range(height):
            value = grid[row][column]
            if value != 0:
                output[row][column] = value
                break
    return output
