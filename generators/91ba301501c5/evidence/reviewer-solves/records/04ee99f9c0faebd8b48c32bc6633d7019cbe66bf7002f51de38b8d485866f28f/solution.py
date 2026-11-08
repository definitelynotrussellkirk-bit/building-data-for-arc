"""Visible-example solution for task 91ba301501c5."""


def solve(grid):
    """Extend colored markers vertically relative to the solid divider row.

    Color 1 grows away from the divider; color 2 grows toward the divider.
    The solid color-5 row and every original marker are preserved.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_rows = [
        r for r, row in enumerate(grid)
        if row and all(value == 5 for value in row)
    ]
    if len(divider_rows) != 1:
        raise ValueError("expected exactly one solid color-5 divider row")
    divider = divider_rows[0]

    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        if r == divider:
            continue
        for c, value in enumerate(row):
            if value not in (1, 2):
                continue

            if r < divider:
                # Above the divider: 1 grows upward, 2 grows downward.
                start, stop = (0, r) if value == 1 else (r, divider - 1)
            else:
                # Below the divider: 1 grows downward, 2 grows upward.
                start, stop = (r, height - 1) if value == 1 else (divider + 1, r)

            for rr in range(start, stop + 1):
                result[rr][c] = value

    return result
