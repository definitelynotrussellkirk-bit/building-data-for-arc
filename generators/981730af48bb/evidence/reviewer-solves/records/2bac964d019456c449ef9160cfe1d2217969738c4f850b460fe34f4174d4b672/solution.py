def solve(grid):
    """Replace each equal-colored endpoint pair by its row-wise midpoint."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row_index, row in enumerate(grid):
        endpoints = [(column, value) for column, value in enumerate(row) if value]
        if len(endpoints) != 2:
            continue
        (left, color), (right, other_color) = endpoints
        if color == other_color and (left + right) % 2 == 0:
            output[row_index][(left + right) // 2] = color
    return output
