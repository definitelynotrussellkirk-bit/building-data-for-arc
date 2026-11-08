"""Visible-example solution for blind task 5000bcb83fa9."""


def solve(grid):
    """Replace each nonzero horizontal run by its center cell."""
    output = [[0 for _ in row] for row in grid]

    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            color = row[column]
            if color == 0:
                column += 1
                continue

            start = column
            column += 1
            while column < len(row) and row[column] == color:
                column += 1
            end = column - 1
            output[row_index][(start + end) // 2] = color

    return output
