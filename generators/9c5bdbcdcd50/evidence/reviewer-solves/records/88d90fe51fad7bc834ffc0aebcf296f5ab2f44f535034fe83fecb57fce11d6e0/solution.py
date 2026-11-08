from bisect import bisect_left


def solve(grid):
    """Recolor regions made by full gray separator rows and columns."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    separator_rows = [r for r, row in enumerate(grid) if all(value == 3 for value in row)]
    separator_cols = [
        c for c in range(width) if all(grid[r][c] == 3 for r in range(height))
    ]

    result = [row[:] for row in grid]
    last_row_band = len(separator_rows)
    last_col_band = len(separator_cols)
    corner_colors = {
        (0, 0): 2,
        (0, last_col_band): 4,
        (last_row_band, 0): 1,
        (last_row_band, last_col_band): 8,
    }

    for r in range(height):
        if r in separator_rows:
            continue
        row_band = bisect_left(separator_rows, r)
        for c in range(width):
            if c in separator_cols:
                continue
            col_band = bisect_left(separator_cols, c)
            if (row_band, col_band) in corner_colors:
                result[r][c] = corner_colors[(row_band, col_band)]
            elif 0 < row_band < last_row_band and 0 < col_band < last_col_band:
                result[r][c] = 7
            else:
                result[r][c] = 0

    return result
