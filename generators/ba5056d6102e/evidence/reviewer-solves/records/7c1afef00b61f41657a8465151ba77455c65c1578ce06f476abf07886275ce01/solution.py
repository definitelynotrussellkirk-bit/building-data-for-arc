def solve(grid):
    """Intersect the two panels separated by a solid row of color 5."""
    separator = next(
        row_index
        for row_index, row in enumerate(grid)
        if row and all(value == 5 for value in row)
    )
    upper = grid[:separator]
    lower = grid[separator + 1 :]

    if len(upper) != len(lower) or any(
        len(upper_row) != len(lower_row)
        for upper_row, lower_row in zip(upper, lower)
    ):
        raise ValueError("expected equal-sized panels around the separator")

    return [
        [8 if upper_value != 0 and lower_value != 0 else 0
         for upper_value, lower_value in zip(upper_row, lower_row)]
        for upper_row, lower_row in zip(upper, lower)
    ]
