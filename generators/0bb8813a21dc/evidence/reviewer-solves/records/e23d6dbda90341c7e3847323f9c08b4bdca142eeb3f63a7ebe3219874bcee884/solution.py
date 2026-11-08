"""Visible-example solution for reviewer-authored task 0bb8813a21dc.

For each row, preserve the zero mask and recolor every nonzero cell with the
row's leftmost nonzero color. Empty rows remain unchanged.
"""


def solve(grid):
    result = []
    for row in grid:
        leader = next((value for value in row if value != 0), None)
        if leader is None:
            result.append(list(row))
        else:
            result.append([leader if value != 0 else 0 for value in row])
    return result
