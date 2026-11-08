"""Visible-example solution for blind task a0ff437161da."""


def solve(grid):
    """Fill the rectangle from the lone non-8 marker to its nearest corner.

    Vertical and horizontal ties choose the top and left edges respectively,
    matching the visible centered example.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 8
    ]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one non-8 marker, found {len(markers)}")

    marker_row, marker_col, marker_color = markers[0]
    top_is_nearer = marker_row <= (height - 1 - marker_row)
    left_is_nearer = marker_col <= (width - 1 - marker_col)

    row_start, row_stop = ((0, marker_row + 1) if top_is_nearer
                           else (marker_row, height))
    col_start, col_stop = ((0, marker_col + 1) if left_is_nearer
                           else (marker_col, width))

    output = [row[:] for row in grid]
    for r in range(row_start, row_stop):
        for c in range(col_start, col_stop):
            output[r][c] = marker_color
    return output
