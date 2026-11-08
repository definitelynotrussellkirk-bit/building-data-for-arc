"""Visible-example solution for the row-wave task."""


def solve(grid):
    if not grid:
        return []
    width = len(grid[0])
    active = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    if not active:
        return [row[:] for row in grid]

    anchor = active[-1]
    shifts = (0, -1, 0, 1)
    output = [[0] * width for _ in grid]
    for r, row in enumerate(grid):
        if not any(value != 0 for value in row):
            continue
        shift = shifts[(anchor - r) % 4]
        for c, value in enumerate(row):
            if value == 0:
                continue
            destination = c + shift
            if 0 <= destination < width:
                output[r][destination] = value
    return output
