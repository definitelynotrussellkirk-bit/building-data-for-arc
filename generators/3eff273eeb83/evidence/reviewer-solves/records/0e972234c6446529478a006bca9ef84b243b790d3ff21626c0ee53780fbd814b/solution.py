def solve(grid):
    """Rotate the color-2 radial line clockwise about 5; recolor its source to 3."""
    height = len(grid)
    width = len(grid[0])
    pivot = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    )
    pivot_row, pivot_col = pivot
    output = [[0 for _ in range(width)] for _ in range(height)]
    output[pivot_row][pivot_col] = 5
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2:
                continue
            output[row][col] = 3
            delta_row = row - pivot_row
            delta_col = col - pivot_col
            rotated_row = pivot_row + delta_col
            rotated_col = pivot_col - delta_row
            output[rotated_row][rotated_col] = 2
    return output
