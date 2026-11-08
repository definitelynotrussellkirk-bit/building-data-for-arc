"""Visible-example solution for dc050b56cac4."""


def solve(grid):
    h = len(grid)
    w = len(grid[0])

    cross_row = next(
        r
        for r in range(h)
        if len(set(grid[r])) == 1 and grid[r][0] not in (0, 5)
    )
    cross_col = next(
        c
        for c in range(w)
        if len({grid[r][c] for r in range(h)}) == 1
        and grid[0][c] not in (0, 5)
    )
    color = grid[cross_row][cross_col]
    n_gray = sum(value == 5 for row in grid for value in row)
    new_row = cross_row + n_gray
    new_col = cross_col - n_gray

    return [
        [color if r == new_row or c == new_col else 0 for c in range(w)]
        for r in range(h)
    ]
