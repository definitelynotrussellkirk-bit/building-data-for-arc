"""Visible-only solution for the reviewer solve episode."""


def solve(grid):
    """Keep only rows with exactly two matching nonzero markers and join them."""
    result = []
    for row in grid:
        nonzero = [(column, value) for column, value in enumerate(row) if value != 0]
        output_row = [0] * len(row)
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            left = nonzero[0][0]
            right = nonzero[1][0]
            color = nonzero[0][1]
            for column in range(left, right + 1):
                output_row[column] = color
        result.append(output_row)
    return result
