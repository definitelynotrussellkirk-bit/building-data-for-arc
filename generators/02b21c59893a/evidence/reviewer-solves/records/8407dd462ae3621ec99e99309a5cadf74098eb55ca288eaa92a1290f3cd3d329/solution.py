def solve(grid):
    """Translate every non-anchor payload cell from blue to the last red."""
    height = len(grid)
    width = len(grid[0])
    blue = None
    reds = []
    payload = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 1:
                blue = (row, col)
            elif value == 2:
                reds.append((row, col))
            elif value != 0:
                payload.append((row, col, value))
    if blue is None or not reds:
        raise ValueError("expected a blue source and at least one red destination")
    destination = reds[-1]
    output = [[0 for _ in range(width)] for _ in range(height)]
    output[destination[0]][destination[1]] = 2
    for row, col, value in payload:
        moved_row = destination[0] + row - blue[0]
        moved_col = destination[1] + col - blue[1]
        if 0 <= moved_row < height and 0 <= moved_col < width:
            output[moved_row][moved_col] = value
    return output
