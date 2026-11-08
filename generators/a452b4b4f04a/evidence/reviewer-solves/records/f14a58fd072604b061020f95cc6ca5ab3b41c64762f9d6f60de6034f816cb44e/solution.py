def solve(grid):
    """Complete each nonzero color's rectangular outline."""
    result = [row[:] for row in grid]
    positions = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    for color, points in positions.items():
        top = min(row for row, _ in points)
        bottom = max(row for row, _ in points)
        left = min(column for _, column in points)
        right = max(column for _, column in points)
        for column in range(left, right + 1):
            result[top][column] = color
            result[bottom][column] = color
        for row in range(top, bottom + 1):
            result[row][left] = color
            result[row][right] = color

    return result
