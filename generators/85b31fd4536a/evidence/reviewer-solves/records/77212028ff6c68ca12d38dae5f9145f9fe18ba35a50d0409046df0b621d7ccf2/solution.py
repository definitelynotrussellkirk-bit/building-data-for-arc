"""Visible-example solution for the blind ARC episode."""


def solve(grid):
    """Mask the right panel with the binary panel left of the 9 divider."""
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separators = [
        column
        for column in range(1, width - 1)
        if all(row[column] == 9 for row in grid)
        and column == width - column - 1
    ]
    if len(separators) != 1:
        raise ValueError("expected one full-height 9 divider between equal-width panels")

    divider = separators[0]
    result = []
    for row in grid:
        mask = row[:divider]
        colors = row[divider + 1 :]
        result.append([color if flag == 1 else 0 for flag, color in zip(mask, colors)])
    return result
