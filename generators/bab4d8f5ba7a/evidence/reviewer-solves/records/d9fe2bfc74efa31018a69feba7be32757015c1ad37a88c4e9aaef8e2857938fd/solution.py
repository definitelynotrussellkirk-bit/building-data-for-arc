"""Visible-example solution for blind task bab4d8f5ba7a."""


def solve(grid):
    """Recolor gray markers in a row from that row's left-edge color key.

    Rows whose first cell is a non-background, non-gray color act as keyed rows:
    every gray (8) cell in that row is changed to the key color.  Other cells and
    unkeyed rows are left unchanged.
    """
    result = [list(row) for row in grid]
    for row in result:
        if row and row[0] not in (0, 8):
            key = row[0]
            for col, value in enumerate(row):
                if value == 8:
                    row[col] = key
    return result
