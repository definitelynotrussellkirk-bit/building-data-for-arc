from collections import Counter


def solve(grid):
    """Color regions defined by the outermost complete separator lines.

    The separator lattice is preserved.  The four exterior corner regions are
    colored 2/4/1/8 (top-left/top-right/bottom-left/bottom-right), while every
    background cell inside the outermost separator rectangle is colored 7.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    # Complete non-background rows and columns are the separator lines.  Infer
    # the separator color from all complete lines so the implementation does
    # not depend on the examples always using a particular color value.
    full_row_colors = [
        row[0]
        for row in grid
        if row and row[0] != 0 and all(value == row[0] for value in row)
    ]
    full_col_colors = []
    for col in range(width):
        value = grid[0][col]
        if value != 0 and all(grid[row][col] == value for row in range(height)):
            full_col_colors.append(value)

    candidates = full_row_colors + full_col_colors
    if not candidates:
        return [row[:] for row in grid]
    separator = Counter(candidates).most_common(1)[0][0]

    separator_rows = [
        row
        for row in range(height)
        if all(grid[row][col] == separator for col in range(width))
    ]
    separator_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == separator for row in range(height))
    ]
    if len(separator_rows) < 2 or len(separator_cols) < 2:
        return [row[:] for row in grid]

    top, bottom = separator_rows[0], separator_rows[-1]
    left, right = separator_cols[0], separator_cols[-1]
    result = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if top < row < bottom and left < col < right:
                result[row][col] = 7
            elif row < top and col < left:
                result[row][col] = 2
            elif row < top and col > right:
                result[row][col] = 4
            elif row > bottom and col < left:
                result[row][col] = 1
            elif row > bottom and col > right:
                result[row][col] = 8

    return result
