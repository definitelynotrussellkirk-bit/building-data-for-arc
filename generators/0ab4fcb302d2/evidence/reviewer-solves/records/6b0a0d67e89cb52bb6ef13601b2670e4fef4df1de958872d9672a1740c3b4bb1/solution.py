def solve(grid):
    """Expand the 3x3 coded input into two 4x4 color blocks."""
    if not isinstance(grid, list) or len(grid) != 3:
        raise ValueError("expected a 3x3 grid")
    if any(not isinstance(row, list) or len(row) != 3 for row in grid):
        raise ValueError("expected a rectangular 3x3 grid")

    gap_rows = [r for r in range(3) if all(grid[r][c] == 0 for c in range(3))]
    gap_cols = [c for c in range(3) if all(grid[r][c] == 0 for r in range(3))]
    if len(gap_rows) != 1 or len(gap_cols) != 1:
        raise ValueError("expected one all-zero row and one all-zero column")
    gap_row, gap_col = gap_rows[0], gap_cols[0]

    rows = [r for r in range(3) if r != gap_row]
    cols = [c for c in range(3) if c != gap_col]
    code = [grid[r][c] for r in rows for c in cols]
    marker_indices = [i for i, value in enumerate(code) if value == 2]
    if len(marker_indices) != 1:
        raise ValueError("expected one red marker")
    fill_values = [value for value in code if value != 2]
    if len(fill_values) != 3 or len(set(fill_values)) != 1:
        raise ValueError("expected three equal fill-color cells")
    fill = fill_values[0]

    marker = marker_indices[0]
    marker_on_main_diagonal = marker in (0, 3)

    # The input gap at index 0/1/2 becomes output gutter 0/4/8.  The two
    # remaining input rows and columns each expand to contiguous groups of four.
    row_starts = [1, 5] if gap_row == 0 else [0, 5] if gap_row == 1 else [0, 4]
    col_starts = [1, 5] if gap_col == 0 else [0, 5] if gap_col == 1 else [0, 4]
    block_positions = (
        [(row_starts[0], col_starts[0]), (row_starts[1], col_starts[1])]
        if marker_on_main_diagonal
        else [(row_starts[0], col_starts[1]), (row_starts[1], col_starts[0])]
    )

    output = [[0 for _ in range(9)] for _ in range(9)]
    for row0, col0 in block_positions:
        for row in range(row0, row0 + 4):
            for col in range(col0, col0 + 4):
                output[row][col] = fill
    return output
