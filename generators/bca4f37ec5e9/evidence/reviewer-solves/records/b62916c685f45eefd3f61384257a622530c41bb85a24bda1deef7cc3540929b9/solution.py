"""Visible-only solver for the prepared bca4f37ec5e9 episode."""


def solve(grid):
    """Repeat the contiguous nonzero row band across the grid height.

    The original band stays at its observed row positions, so the repetition's
    vertical phase is anchored at the band's first source row.
    """
    if not grid:
        return []

    occupied_rows = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    if not occupied_rows:
        return [row[:] for row in grid]

    start = occupied_rows[0]
    end = occupied_rows[-1]
    band = [row[:] for row in grid[start : end + 1]]
    period = len(band)

    return [band[(r - start) % period][:] for r in range(len(grid))]
