"""Visible-example solution for ARC task 33275a4aae3e."""


def _longest_run_in_column(grid, col, foreground):
    best = run = 0
    for row in grid:
        if row[col] == foreground:
            run += 1
            if run > best:
                best = run
        else:
            run = 0
    return best


def solve(grid):
    """Color the rectangular grid interior 2 and the exterior background 3.

    The original nonzero line color is preserved.  The rectangle is delimited by
    the outermost long vertical lines and the outermost horizontal lines that
    span between those vertical boundaries.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height, width = len(grid), len(grid[0])
    foregrounds = {value for row in grid for value in row if value != 0}
    if len(foregrounds) != 1:
        raise ValueError("expected exactly one nonzero line color")
    foreground = next(iter(foregrounds))

    # Genuine vertical construction lines occupy well over half the height;
    # short vertical-looking pieces arise only from decorative stubs.
    minimum_run = height // 2
    verticals = [
        col
        for col in range(width)
        if _longest_run_in_column(grid, col, foreground) >= minimum_run
    ]
    if len(verticals) < 2:
        raise ValueError("could not locate the two vertical rectangle boundaries")
    left, right = min(verticals), max(verticals)

    spanning_rows = [
        row
        for row in range(height)
        if all(grid[row][col] == foreground for col in range(left, right + 1))
    ]
    if len(spanning_rows) < 2:
        raise ValueError("could not locate the two horizontal rectangle boundaries")
    top, bottom = min(spanning_rows), max(spanning_rows)

    result = []
    for row_index, row in enumerate(grid):
        out_row = []
        for col_index, value in enumerate(row):
            if value != 0:
                out_row.append(value)
            elif top < row_index < bottom and left < col_index < right:
                out_row.append(2)
            else:
                out_row.append(3)
        result.append(out_row)
    return result
