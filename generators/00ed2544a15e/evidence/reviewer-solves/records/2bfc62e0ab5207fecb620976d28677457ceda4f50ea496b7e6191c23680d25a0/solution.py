from copy import deepcopy


def solve(grid):
    """Join eligible red endpoints with cyan along their shared row or column."""
    output = deepcopy(grid)
    red = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]

    for index, first in enumerate(red):
        for second in red[index + 1 :]:
            r1, c1 = first
            r2, c2 = second
            if r1 == r2:
                lo, hi = sorted((c1, c2))
                cells = [(r1, col) for col in range(lo, hi + 1)]
            elif c1 == c2:
                lo, hi = sorted((r1, r2))
                cells = [(row, c1) for row in range(lo, hi + 1)]
            else:
                continue

            values = [grid[row][col] for row, col in cells]
            if values.count(2) == 2 and all(value in (0, 2) for value in values):
                for row, col in cells[1:-1]:
                    output[row][col] = 8

    return output
