"""Visible-only solution for the assigned blind ARC task."""


def solve(grid):
    """Fill the horizontal span when a row contains one matching endpoint pair.

    A row changes only when it has exactly two nonzero cells and both cells have
    the same color.  All cells between those endpoints become that color.
    Other rows are copied unchanged.
    """
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        marked = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(marked) != 2 or marked[0][1] != marked[1][1]:
            continue
        left, color = marked[0]
        right, _ = marked[1]
        output[row_index][left : right + 1] = [color] * (right - left + 1)
    return output
