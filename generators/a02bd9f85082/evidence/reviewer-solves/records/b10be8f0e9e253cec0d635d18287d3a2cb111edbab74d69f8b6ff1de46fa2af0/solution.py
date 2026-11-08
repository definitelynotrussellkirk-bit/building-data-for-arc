"""Visible-example solution for blind task a02bd9f85082."""


def solve(grid):
    """Paint four quarter-turn copies of the marked shape around color 5.

    The four colors in the top-left header correspond to rotations of
    0, 90, 180, and 270 degrees clockwise.  Copies are painted in that
    order, so later rotations win where copies overlap.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    # The header is the first four cells of row zero in every visible case.
    colors = grid[0][:4]

    pivots = [
        (r, c)
        for r in range(1, height)
        for c in range(width)
        if grid[r][c] == 5
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected one pivot outside the header, found {len(pivots)}")
    pr, pc = pivots[0]

    shape = [
        (r - pr, c - pc)
        for r in range(1, height)
        for c in range(width)
        if grid[r][c] not in (0, 5)
    ]

    def rotate(dr, dc, turns):
        for _ in range(turns):
            dr, dc = dc, -dr
        return dr, dc

    for turns, color in enumerate(colors):
        for dr, dc in shape:
            rr, cc = rotate(dr, dc, turns)
            r, c = pr + rr, pc + cc
            if not (0 <= r < height and 0 <= c < width):
                raise ValueError("rotated copy falls outside the grid")
            out[r][c] = color

    out[pr][pc] = 5
    return out
