def solve(grid):
    """Connect aligned cells of each nonzero color with straight segments."""
    output = [row[:] for row in grid]
    positions = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    # The lower-numbered color is the rigid frame in the visible examples, so
    # draw it first and only paint background cells thereafter.
    for color in sorted(positions):
        rows = {}
        columns = {}
        for row_index, column_index in positions[color]:
            rows.setdefault(row_index, []).append(column_index)
            columns.setdefault(column_index, []).append(row_index)

        for row_index, column_indices in rows.items():
            if len(column_indices) >= 2:
                for column_index in range(min(column_indices), max(column_indices) + 1):
                    if output[row_index][column_index] in (0, color):
                        output[row_index][column_index] = color

        for column_index, row_indices in columns.items():
            if len(row_indices) >= 2:
                for row_index in range(min(row_indices), max(row_indices) + 1):
                    if output[row_index][column_index] in (0, color):
                        output[row_index][column_index] = color

    return output
