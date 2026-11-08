"""Visible-example-only solution for ARC task 1ce259f214c8."""


def solve(grid):
    """XOR the two same-sized panels separated by a solid color-5 column.

    A cell is 8 exactly when one panel has a nonzero cell and the other has
    background 0.  Cells occupied in both panels, or in neither, become 0.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("input grid must be rectangular")

    separators = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError("expected exactly one full-height separator of color 5")

    separator = separators[0]
    left_width = separator
    right_width = width - separator - 1
    if left_width != right_width:
        raise ValueError("expected equal-width panels around the separator")

    result = []
    for row in grid:
        left = row[:separator]
        right = row[separator + 1 :]
        result.append([
            8 if ((a == 0) != (b == 0)) else 0
            for a, b in zip(left, right)
        ])
    return result
