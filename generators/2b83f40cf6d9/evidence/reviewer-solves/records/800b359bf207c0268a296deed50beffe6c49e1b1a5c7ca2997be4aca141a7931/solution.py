def solve(grid):
    """Join equal-color endpoints by row-first alternating axis steps."""
    pairs = {}
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color:
                pairs.setdefault(color, []).append((row, column))
    answer = [row[:] for row in grid]
    for color, points in pairs.items():
        if len(points) != 2:
            continue
        (row, column), (end_row, end_column) = points
        answer[row][column] = color
        while (row, column) != (end_row, end_column):
            if row != end_row:
                row += 1 if row < end_row else -1
                answer[row][column] = color
            if column != end_column:
                column += 1 if column < end_column else -1
                answer[row][column] = color
    return answer
