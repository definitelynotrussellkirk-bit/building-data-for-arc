from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the interior between a row's rightmost marker and its mirror.

    The global rightmost non-background column defines a vertical mirror axis
    halfway between that column and the next one.  On each occupied row, the
    rightmost marker is the left boundary; boundary cells themselves disappear
    and the cells strictly between it and its mirror are filled with its color.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0]) if grid[0] else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    occupied = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return out

    axis_left = max(c for _, c in occupied)
    for r, row in enumerate(grid):
        row_markers = [c for c, value in enumerate(row) if value != 0]
        if not row_markers:
            continue
        left_boundary = max(row_markers)
        color = row[left_boundary]
        right_boundary = 2 * axis_left + 1 - left_boundary
        for c in range(left_boundary + 1, right_boundary):
            if 0 <= c < width:
                out[r][c] = color

    return out
