def solve(grid):
    """Keep cells that have exactly one orthogonal neighbor of the same color."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            degree = 0
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + drow, col + dcol
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == color:
                    degree += 1
            if degree == 1:
                output[row][col] = color
    return output
