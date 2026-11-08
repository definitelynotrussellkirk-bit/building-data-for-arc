"""Visible-example solution for ARC task 27bc4c66eed7."""


def solve(grid):
    """Replace every maximal horizontal nonzero run by its right-middle cell."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    for row_index, row in enumerate(grid):
        column = 0
        while column < width:
            color = row[column]
            if color == 0:
                column += 1
                continue

            start = column
            while column + 1 < width and row[column + 1] == color:
                column += 1
            end = column
            midpoint = start + (end - start + 1) // 2
            output[row_index][midpoint] = color
            column += 1

    return output
