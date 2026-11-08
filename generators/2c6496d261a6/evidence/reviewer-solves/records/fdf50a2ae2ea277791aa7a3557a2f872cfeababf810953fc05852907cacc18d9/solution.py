def solve(grid):
    """Keep exactly the non-background colors confined to one row."""
    rows_by_color = {}
    for row_index, row in enumerate(grid):
        for value in row:
            if value != 0:
                rows_by_color.setdefault(value, set()).add(row_index)

    keep = {value for value, rows in rows_by_color.items() if len(rows) == 1}
    return [
        [value if value in keep else 0 for value in row]
        for row in grid
    ]
