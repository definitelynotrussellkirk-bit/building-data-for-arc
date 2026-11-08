from copy import deepcopy


def solve(grid):
    """Fill background cells sharing both coordinate parities with the marker."""
    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if len(markers) != 1:
        raise ValueError(f"expected one non-0/non-5 marker, found {len(markers)}")
    marker_row, marker_col, marker_color = markers[0]
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and r % 2 == marker_row % 2 and c % 2 == marker_col % 2:
                out[r][c] = marker_color
    return out
