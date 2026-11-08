def solve(grid):
    """Move the colored cross down/left by the number of gray markers."""
    h = len(grid)
    w = len(grid[0])
    gray_count = sum(value == 5 for row in grid for value in row)

    full_rows = []
    for r, row in enumerate(grid):
        color = row[0]
        if color not in (0, 5) and all(value == color for value in row):
            full_rows.append((r, color))

    full_cols = []
    for c in range(w):
        color = grid[0][c]
        if color not in (0, 5) and all(grid[r][c] == color for r in range(h)):
            full_cols.append((c, color))

    if len(full_rows) != 1 or len(full_cols) != 1:
        raise ValueError("expected one complete colored row and column")
    cross_row, row_color = full_rows[0]
    cross_col, col_color = full_cols[0]
    if row_color != col_color:
        raise ValueError("cross row and column must have the same color")

    new_row = cross_row + gray_count
    new_col = cross_col - gray_count
    if not (0 <= new_row < h and 0 <= new_col < w):
        raise ValueError("shifted cross would leave the grid")

    return [
        [row_color if r == new_row or c == new_col else 0 for c in range(w)]
        for r in range(h)
    ]
