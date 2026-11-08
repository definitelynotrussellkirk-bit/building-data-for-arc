def solve(grid):
    """Extend every colored seed toward its nearest vertical and horizontal edges.

    A tie is resolved toward the bottom/right.  Seeds are considered in row-major
    order; first paint wins if a malformed input makes two rays overlap.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    emitters = [
        (row, col, color)
        for row, values in enumerate(grid)
        for col, color in enumerate(values)
        if color != 0
    ]
    output = [[0 for _ in range(width)] for _ in range(height)]

    for row, col, color in emitters:
        vertical_rows = range(0, row + 1) if 2 * row < height - 1 else range(row, height)
        horizontal_cols = range(0, col + 1) if 2 * col < width - 1 else range(col, width)

        for out_row in vertical_rows:
            if output[out_row][col] == 0:
                output[out_row][col] = color
        for out_col in horizontal_cols:
            if output[row][out_col] == 0:
                output[row][out_col] = color

    return output
