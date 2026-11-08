def solve(grid):
    """Complete the perimeter of each nonzero color's bounding rectangle.

    Colors are processed in the order of their first visible cell, so a later
    pair is visible where two rectangle borders overlap.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    positions = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    for color, cells in positions.items():
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(columns), max(columns)

        for column in range(left, right + 1):
            output[top][column] = color
            output[bottom][column] = color
        for row in range(top, bottom + 1):
            output[row][left] = color
            output[row][right] = color

    return output
