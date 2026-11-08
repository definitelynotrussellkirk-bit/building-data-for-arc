from __future__ import annotations


def solve(grid):
    """Fill background cells sharing the marker's row/column parity pair."""
    marker = None
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in (0, 5):
                marker = (row, col, value)
                break
        if marker is not None:
            break
    if marker is None:
        return [list(row) for row in grid]

    marker_row, marker_col, marker_color = marker
    result = [list(row) for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (
                value == 0
                and row % 2 == marker_row % 2
                and col % 2 == marker_col % 2
            ):
                result[row][col] = marker_color
    return result
