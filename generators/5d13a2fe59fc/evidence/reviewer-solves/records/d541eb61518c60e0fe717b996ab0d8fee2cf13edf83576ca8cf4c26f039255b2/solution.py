def solve(grid):
    """Paint a down-right diagonal ray from every nonzero top-row seed."""
    if not grid or not grid[0]:
        return [] if not grid else [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for start_col, color in enumerate(grid[0]):
        if color == 0:
            continue
        row, col = 0, start_col
        while row < height and col < width:
            output[row][col] = color
            row += 1
            col += 1
    return output
