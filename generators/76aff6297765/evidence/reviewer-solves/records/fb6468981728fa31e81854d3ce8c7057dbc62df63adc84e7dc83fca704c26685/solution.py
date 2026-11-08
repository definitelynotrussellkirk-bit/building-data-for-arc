def solve(grid):
    """Overlay the two panels and mark cells empty in both with azure (8)."""
    height = len(grid)
    width = len(grid[0])

    separator = None
    for row_index, row in enumerate(grid):
        if (
            row_index * 2 + 1 == height
            and len(row) == width
            and row[0] != 0
            and all(value == row[0] for value in row)
        ):
            separator = row_index
            break

    if separator is None:
        separator = height // 2

    top = grid[:separator]
    bottom = grid[separator + 1 :]
    if len(top) != len(bottom):
        raise ValueError("expected two equal-height panels separated by one row")

    return [
        [8 if upper == 0 and lower == 0 else 0 for upper, lower in zip(top_row, bottom_row)]
        for top_row, bottom_row in zip(top, bottom)
    ]
