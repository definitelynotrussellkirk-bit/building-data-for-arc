def solve(grid):
    """Fill zero gaps bounded by gray (8) and one colored cell.

    Each row is treated independently.  Between every pair of consecutive
    nonzero cells, fill the intervening zeros only when exactly one endpoint is
    gray (8); use the other endpoint's color.  Gray-gray and color-color gaps
    remain unchanged.
    """
    result = [list(row) for row in grid]

    for row_index, row in enumerate(grid):
        nonzero_columns = [column for column, value in enumerate(row) if value != 0]
        for left_column, right_column in zip(nonzero_columns, nonzero_columns[1:]):
            left_value = row[left_column]
            right_value = row[right_column]

            if (left_value == 8) == (right_value == 8):
                continue

            fill_value = right_value if left_value == 8 else left_value
            for column in range(left_column + 1, right_column):
                result[row_index][column] = fill_value

    return result
