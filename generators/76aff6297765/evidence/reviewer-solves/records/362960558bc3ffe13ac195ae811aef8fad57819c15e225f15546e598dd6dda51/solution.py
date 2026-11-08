"""Visible-example solution for task 76aff6297765."""


def solve(grid):
    """Compare the two panels split by a solid 7 row.

    Return 8 exactly where the aligned cells in both panels are zero.
    """
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    separators = [i for i, row in enumerate(grid) if row == [7] * width]
    if len(separators) != 1:
        raise ValueError("expected one full separator row of 7s")
    split = separators[0]
    top = grid[:split]
    bottom = grid[split + 1 :]
    if len(top) != len(bottom):
        raise ValueError("panels must have equal height")
    return [
        [8 if upper == 0 and lower == 0 else 0 for upper, lower in zip(a, b)]
        for a, b in zip(top, bottom)
    ]
