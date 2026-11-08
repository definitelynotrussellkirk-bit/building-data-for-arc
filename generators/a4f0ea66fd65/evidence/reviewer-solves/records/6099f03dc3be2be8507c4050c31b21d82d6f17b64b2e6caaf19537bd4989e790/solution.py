"""Visible-only solution for blind task a4f0ea66fd65."""


def solve(grid):
    """Translate the color-8 motif by the vector from marker 2 to marker 3.

    The translated motif is painted color 1. Existing cells at translated
    locations are overwritten, as required by the visible examples.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [row[:] for row in grid]

    marker_2 = None
    marker_3 = None
    source_cells = []

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                marker_2 = (r, c)
            elif value == 3:
                marker_3 = (r, c)
            elif value == 8:
                source_cells.append((r, c))

    if marker_2 is None or marker_3 is None:
        return out

    dr = marker_3[0] - marker_2[0]
    dc = marker_3[1] - marker_2[1]
    for r, c in source_cells:
        rr, cc = r + dr, c + dc
        if 0 <= rr < rows and 0 <= cc < cols:
            out[rr][cc] = 1

    return out
