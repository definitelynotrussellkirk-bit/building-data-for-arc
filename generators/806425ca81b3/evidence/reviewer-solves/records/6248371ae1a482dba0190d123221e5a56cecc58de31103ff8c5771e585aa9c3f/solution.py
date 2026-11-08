def solve(grid):
    result = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        positions = {}
        for column, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append(column)
        for color in sorted(positions):
            anchors = positions[color]
            for column in range(anchors[0] + 1, anchors[-1]):
                if row[column] == 0 and result[row_index][column] == 0:
                    result[row_index][column] = color
    return result
