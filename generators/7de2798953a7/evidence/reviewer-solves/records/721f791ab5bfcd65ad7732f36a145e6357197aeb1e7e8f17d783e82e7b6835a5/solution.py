def solve(grid):
    """Extend each same-colored horizontal pair with the observed dash pattern."""
    result = [row[:] for row in grid]

    for row_index, row in enumerate(grid):
        positions_by_color = {}
        for column, color in enumerate(row):
            if color != 0:
                positions_by_color.setdefault(color, []).append(column)

        for color, columns in positions_by_color.items():
            if len(columns) != 2:
                continue
            left, right = columns
            for column in range(left + 1, right, 2):
                if result[row_index][column] == 0:
                    result[row_index][column] = color

    return result
