def solve(grid):
    """Move the green shape by the vector from the blue marker to the red marker.

    The translated shape is recolored azure; cells that move outside the grid are
    clipped.  The original shape and both markers disappear.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0

    blue = red = None
    green = []
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 1:
                blue = (row_index, column_index)
            elif value == 2:
                red = (row_index, column_index)
            elif value == 3:
                green.append((row_index, column_index))

    if blue is None or red is None:
        raise ValueError("expected one blue marker and one red marker")

    row_shift = red[0] - blue[0]
    column_shift = red[1] - blue[1]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row_index, column_index in green:
        moved_row = row_index + row_shift
        moved_column = column_index + column_shift
        if 0 <= moved_row < height and 0 <= moved_column < width:
            output[moved_row][moved_column] = 8
    return output
