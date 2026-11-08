def solve(grid):
    """Rotate every non-background cell 90° clockwise about the unique 9 cell."""
    height = len(grid)
    width = len(grid[0])

    anchors = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if len(anchors) != 1:
        raise ValueError("expected exactly one color-9 rotation center")

    center_row, center_col = anchors[0]
    result = [[0 for _ in range(width)] for _ in range(height)]
    result[center_row][center_col] = 9

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 9):
                continue

            delta_row = row - center_row
            delta_col = col - center_col
            rotated_row = center_row + delta_col
            rotated_col = center_col - delta_row

            if not (0 <= rotated_row < height and 0 <= rotated_col < width):
                raise ValueError("rotated cell falls outside the grid")
            result[rotated_row][rotated_col] = color

    return result
