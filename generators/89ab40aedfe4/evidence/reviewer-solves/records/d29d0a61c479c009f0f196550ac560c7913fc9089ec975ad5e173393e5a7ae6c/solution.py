def solve(grid):
    """Stably sort the logical binary columns by their filled-cell count."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    width = len(grid[0])
    # The first row shows every logical glyph in its filled form.  Each glyph
    # is a two-cell nonzero run followed by one or more zero separators.
    starts = [
        col
        for col, value in enumerate(grid[0])
        if value != 0 and (col == 0 or grid[0][col - 1] == 0)
    ]
    value_columns = [start + 1 for start in starts if start + 1 < width]

    order = sorted(
        range(len(value_columns)),
        key=lambda index: sum(
            row[value_columns[index]] != 0 for row in grid
        ),
    )

    result = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        values = [row[col] for col in value_columns]
        for target_index, source_index in enumerate(order):
            result[row_index][value_columns[target_index]] = values[source_index]
    return result
