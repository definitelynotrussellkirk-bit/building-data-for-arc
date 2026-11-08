"""Visible-example solution for blind task c9034f0626e0."""


def solve(grid):
    """Paint the zero cells on the marker's row/column parity lattice.

    The grid contains gray (5), black (0), and one marker cell whose color is
    neither 0 nor 5.  The marker fixes both coordinate parities.  Every black
    cell at a row with the marker's parity *and* a column with the marker's
    parity is recolored with the marker color; all other cells are preserved.
    """
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one non-black/non-gray marker, found {len(markers)}")

    marker_r, marker_c, marker_color = markers[0]
    row_parity = marker_r % 2
    col_parity = marker_c % 2

    return [
        [
            marker_color
            if value == 0 and r % 2 == row_parity and c % 2 == col_parity
            else value
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]
