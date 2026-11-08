def solve(grid):
    """Copy each source corner into a clipped 2x2 patch diagonally opposite."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(cells) != 4:
        raise ValueError("expected four nonzero source cells")

    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    if (len(rows) != 2 or len(cols) != 2
            or rows[1] != rows[0] + 1 or cols[1] != cols[0] + 1):
        raise ValueError("source must be a contiguous 2x2 block")

    br, bc = rows[0], cols[0]
    tl = grid[br][bc]
    tr = grid[br][bc + 1]
    bl = grid[br + 1][bc]
    bottom_right = grid[br + 1][bc + 1]
    if 0 in (tl, tr, bl, bottom_right):
        raise ValueError("source block must be solid")

    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])

    def paint(row_candidates, col_candidates, color):
        for r in row_candidates:
            for c in col_candidates:
                if 0 <= r < h and 0 <= c < w and out[r][c] == 0:
                    out[r][c] = color

    paint((br + 2, br + 3), (bc + 2, bc + 3), tl)
    paint((br + 2, br + 3), (bc - 2, bc - 1), tr)
    paint((br - 2, br - 1), (bc + 2, bc + 3), bl)
    paint((br - 2, br - 1), (bc - 2, bc - 1), bottom_right)
    return out
