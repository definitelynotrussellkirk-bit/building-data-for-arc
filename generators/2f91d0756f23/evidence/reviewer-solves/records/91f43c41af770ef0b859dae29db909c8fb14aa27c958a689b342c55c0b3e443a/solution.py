"""Visible-example solution for blind task 2f91d0756f23."""


def solve(grid):
    """Remove the unary markers and copy the motif by quarter-turns about color 9.

    The number of color-1 cells in the top row is the number of motif
    orientations to retain, including the original orientation.  Each additional
    orientation is a 90-degree clockwise rotation around the unique color-9
    pivot.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    turns = sum(value == 1 for value in grid[0]) if height else 0
    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected one color-9 pivot, found {len(pivots)}")
    pr, pc = pivots[0]

    # Color 1 is an instruction, not part of the output motif.
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 1:
                out[r][c] = 0

    motif = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1, 9)
    ]
    for r, c, value in motif:
        dr, dc = r - pr, c - pc
        for _ in range(max(turns, 1)):
            rr, cc = pr + dr, pc + dc
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value
            dr, dc = dc, -dr  # 90 degrees clockwise in row/column coordinates

    return out
