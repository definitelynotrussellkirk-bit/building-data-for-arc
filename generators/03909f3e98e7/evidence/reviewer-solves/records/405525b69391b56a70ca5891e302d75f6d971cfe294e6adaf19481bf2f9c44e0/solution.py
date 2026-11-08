"""Visible-example solution; authored after disclosed earlier rule exposure."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    cells = [(r, c, value) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value != 0]
    result = [[0] * width for _ in range(height)]
    if not cells:
        return result
    first_row = min(r for r, _, _ in cells)
    last_row = max(r for r, _, _ in cells)
    first_col = min(c for _, c, _ in cells)
    last_col = max(c for _, c, _ in cells)
    row_shift = (height - (last_row - first_row + 1)) // 2 - first_row
    col_shift = (width - (last_col - first_col + 1)) // 2 - first_col
    for r, c, value in cells:
        result[r + row_shift][c + col_shift] = value
    return result
