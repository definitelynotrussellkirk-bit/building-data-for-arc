from __future__ import annotations


def solve(grid):
    """Stamp a red copy of the cyan object after the code-selected pivot rotation."""
    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])

    pivot = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    )
    source = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    ]
    code = next(
        value
        for values in grid
        for value in values
        if 1 <= value <= 4
    )

    prow, pcol = pivot
    for row, col in source:
        drow, dcol = row - prow, col - pcol
        if code == 1:
            target_row, target_col = prow + drow, pcol + dcol
        elif code == 2:
            target_row, target_col = prow + dcol, pcol - drow
        elif code == 3:
            target_row, target_col = prow - drow, pcol - dcol
        else:
            target_row, target_col = prow - dcol, pcol + drow
        if 0 <= target_row < height and 0 <= target_col < width:
            output[target_row][target_col] = 2

    return output
