def solve(grid):
    """Expand the color key in row 0 into cyclic monochrome rows below row 1."""
    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]

    key = grid[0]
    for row_index in range(2, height):
        color = key[(row_index - 2) % width]
        result[row_index] = [color] * width

    return result
