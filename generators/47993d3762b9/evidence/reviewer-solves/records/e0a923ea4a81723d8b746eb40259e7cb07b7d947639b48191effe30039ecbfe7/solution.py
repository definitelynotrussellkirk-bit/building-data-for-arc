def solve(grid):
    positions = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    output = [[0 for _ in row] for row in grid]
    for color, cells in positions.items():
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        for row in {min(rows), max(rows)}:
            for column in {min(columns), max(columns)}:
                output[row][column] = color

    return output
