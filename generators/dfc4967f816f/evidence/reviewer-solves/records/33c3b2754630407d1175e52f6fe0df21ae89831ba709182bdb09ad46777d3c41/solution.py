"""Visible-example solution for the vertical-symmetry tile strip."""


def _segments(width, divider_columns):
    start = 0
    for divider in divider_columns + [width]:
        if divider > start:
            yield start, divider
        start = divider + 1


def solve(grid):
    if not grid or not grid[0]:
        return [[]]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_columns = [
        column
        for column in range(width)
        if all(row[column] == 9 for row in grid)
    ]
    flags = []
    for left, right in _segments(width, divider_columns):
        tile = [row[left:right] for row in grid]
        vertically_symmetric = all(row == row[::-1] for row in tile)
        flags.append(8 if vertically_symmetric else 0)
    return [flags]
