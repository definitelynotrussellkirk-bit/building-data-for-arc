from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend the lone non-8 marker to its nearest corner.

    Manhattan-distance ties use corner order: upper-left, upper-right,
    lower-left, lower-right.  The marker and chosen corner are the inclusive
    opposite corners of the filled rectangle.
    """
    height = len(grid)
    width = len(grid[0])

    marker_row = marker_col = marker_color = None
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 8:
                marker_row, marker_col, marker_color = row, col, color
                break
        if marker_color is not None:
            break

    if marker_color is None:
        return [row[:] for row in grid]

    corners = (
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    )
    corner_row, corner_col = min(
        corners,
        key=lambda corner: abs(marker_row - corner[0]) + abs(marker_col - corner[1]),
    )

    result = [row[:] for row in grid]
    row_lo, row_hi = sorted((marker_row, corner_row))
    col_lo, col_hi = sorted((marker_col, corner_col))
    for row in range(row_lo, row_hi + 1):
        for col in range(col_lo, col_hi + 1):
            result[row][col] = marker_color
    return result
