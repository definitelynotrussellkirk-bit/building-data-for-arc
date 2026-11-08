"""Visible-example solution for blind task 91b531b5d3f4."""


def solve(grid):
    """Recolor 1-cells from the nonzero marker at the top of their column."""
    out = [row[:] for row in grid]
    if not out:
        return out

    header = out[0]
    for r in range(1, len(out)):
        for c, value in enumerate(out[r]):
            if value == 1 and header[c] not in (0, 1):
                out[r][c] = header[c]
    return out
