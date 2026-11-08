from collections import Counter


def solve(grid):
    """Swap the two object colors and move the object's upper bbox half right."""
    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    cells = [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != background
    ]
    colors = list(dict.fromkeys(value for _row, _column, value in cells))
    if len(colors) != 2:
        raise ValueError(f"expected exactly two object colors, found {colors!r}")
    first, second = colors

    rmin = min(row for row, _column, _value in cells)
    rmax = max(row for row, _column, _value in cells)
    cmin = min(column for _row, column, _value in cells)
    cmax = max(column for _row, column, _value in cells)
    midpoint = (rmin + rmax) // 2

    if 0 in colors:
        nonblack_columns = [column for _row, column, value in cells if value != 0]
        shift = max(nonblack_columns) - min(nonblack_columns) + 1
    else:
        shift = cmax - cmin + 1

    output = [[background for _column in range(width)] for _row in range(height)]
    for row, column, value in cells:
        swapped = second if value == first else first
        target_column = column + shift if row <= midpoint else column
        if 0 <= target_column < width:
            output[row][target_column] = swapped
    return output
