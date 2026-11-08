"""Visible-example solution for eb3171637821."""


def _count_runs(indexes):
    count = 0
    previous = None
    for index in indexes:
        if previous is None or index != previous + 1:
            count += 1
        previous = index
    return count


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    colors = sorted({value for row in grid for value in row})

    divider_color = None
    divider_rows = []
    divider_cols = []
    for color in colors:
        rows = [
            row
            for row in range(height)
            if all(grid[row][col] == color for col in range(width))
        ]
        cols = [
            col
            for col in range(width)
            if all(grid[row][col] == color for row in range(height))
        ]
        if rows and cols:
            divider_color = color
            divider_rows = rows
            divider_cols = cols
            break

    if divider_color is None:
        raise ValueError("no divider color forms both complete rows and columns")
    cell_color = next(color for color in colors if color != divider_color)
    blocked_rows = set(divider_rows)
    blocked_cols = set(divider_cols)
    row_bands = _count_runs(row for row in range(height) if row not in blocked_rows)
    col_bands = _count_runs(col for col in range(width) if col not in blocked_cols)
    return [[cell_color] * col_bands for _ in range(row_bands)]
