def solve(grid):
    rows_by_color = {}
    for row_index, row in enumerate(grid):
        for color in row:
            if color != 0:
                rows_by_color.setdefault(color, set()).add(row_index)
    keep = {color for color, rows in rows_by_color.items() if len(rows) == 1}
    return [[color if color in keep else 0 for color in row] for row in grid]
