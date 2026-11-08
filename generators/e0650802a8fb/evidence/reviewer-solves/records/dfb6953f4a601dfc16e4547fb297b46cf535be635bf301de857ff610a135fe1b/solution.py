"""Visible-only solution for the assigned ARC puzzle."""


def solve(grid):
    """Connect each exactly-twice color pair when it lies on a 45° diagonal.

    Colors are handled in row-major order of their first occurrence.  Painting is
    inclusive, so a later eligible pair overwrites an earlier pair at crossings.
    """
    out = [list(row) for row in grid]
    positions = {}

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    for color, points in positions.items():
        if len(points) != 2:
            continue

        (r0, c0), (r1, c1) = points
        dr = r1 - r0
        dc = c1 - c0
        if dr == 0 or abs(dr) != abs(dc):
            continue

        row_step = 1 if dr > 0 else -1
        column_step = 1 if dc > 0 else -1
        for offset in range(abs(dr) + 1):
            out[r0 + offset * row_step][c0 + offset * column_step] = color

    return out
