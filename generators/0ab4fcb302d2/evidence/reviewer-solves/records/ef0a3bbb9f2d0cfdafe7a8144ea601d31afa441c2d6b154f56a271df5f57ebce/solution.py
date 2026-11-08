"""Visible-example solution for the post-repair episode."""


def solve(grid):
    if not isinstance(grid, list) or len(grid) != 3:
        raise ValueError("expected a 3x3 grid")
    if any(not isinstance(row, list) or len(row) != 3 for row in grid):
        raise ValueError("expected a rectangular 3x3 grid")

    gap_rows = [r for r in range(3) if all(grid[r][c] == 0 for c in range(3))]
    gap_cols = [c for c in range(3) if all(grid[r][c] == 0 for r in range(3))]
    if len(gap_rows) != 1 or len(gap_cols) != 1:
        raise ValueError("expected exactly one empty row and column")
    gap_row, gap_col = gap_rows[0], gap_cols[0]

    rows = [r for r in range(3) if r != gap_row]
    cols = [c for c in range(3) if c != gap_col]
    cells = [(r, c) for r in rows for c in cols]
    red_indices = [i for i, (r, c) in enumerate(cells) if grid[r][c] == 2]
    if len(red_indices) != 1:
        raise ValueError("expected one red marker")
    fill = next(
        grid[r][c]
        for r, c in cells
        if grid[r][c] not in (0, 2)
    )

    main_diagonal = red_indices[0] in (0, 3)
    top = 1 if gap_row == 0 else 0
    bottom = 4 if gap_row == 2 else 5
    left = 1 if gap_col == 0 else 0
    right = 4 if gap_col == 2 else 5
    starts = (
        ((top, left), (bottom, right))
        if main_diagonal
        else ((top, right), (bottom, left))
    )

    output = [[0] * 9 for _ in range(9)]
    for row0, col0 in starts:
        for r in range(row0, row0 + 4):
            for c in range(col0, col0 + 4):
                output[r][c] = fill
    return output
