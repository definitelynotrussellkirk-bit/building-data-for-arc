"""Visible-example solution for the post-repair solve episode."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    separator_rows = [
        row for row in range(height) if all(value == 8 for value in grid[row])
    ]
    separator_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(separator_rows) != 2 or len(separator_cols) != 2:
        raise ValueError("expected two full divider rows and columns")

    row_bands = (
        (0, separator_rows[0]),
        (separator_rows[0] + 1, separator_rows[1]),
        (separator_rows[1] + 1, height),
    )
    col_bands = (
        (0, separator_cols[0]),
        (separator_cols[0] + 1, separator_cols[1]),
        (separator_cols[1] + 1, width),
    )
    return [
        [
            int(
                sum(
                    grid[row][col] == 6
                    for row in range(row_start, row_end)
                    for col in range(col_start, col_end)
                )
                >= 2
            )
            for col_start, col_end in col_bands
        ]
        for row_start, row_end in row_bands
    ]
