from __future__ import annotations

from collections import Counter


def _dominant_line_indices(grid):
    height = len(grid)
    width = len(grid[0])
    row_counts = [sum(value != 0 for value in row) for row in grid]
    col_counts = [
        sum(grid[row][col] != 0 for row in range(height))
        for col in range(width)
    ]
    return row_counts.index(max(row_counts)), col_counts.index(max(col_counts))


def _base_and_marker(values):
    counts = Counter(value for value in values if value != 0)
    ordered = counts.most_common()
    return ordered[0][0], ordered[-1][0]


def solve(grid):
    """Expand the two marked crossing strands into their bounded weave."""
    height = len(grid)
    width = len(grid[0])
    strand_row, strand_col = _dominant_line_indices(grid)

    horizontal_values = [value for value in grid[strand_row] if value != 0]
    vertical_values = [
        grid[row][strand_col]
        for row in range(height)
        if grid[row][strand_col] != 0
    ]
    horizontal_base, horizontal_marker = _base_and_marker(horizontal_values)
    vertical_base, vertical_marker = _base_and_marker(vertical_values)

    horizontal_marker_cols = [
        col
        for col, value in enumerate(grid[strand_row])
        if value == horizontal_marker
    ]
    vertical_marker_rows = [
        row
        for row in range(height)
        if grid[row][strand_col] == vertical_marker
    ]
    left, right = min(horizontal_marker_cols), max(horizontal_marker_cols)
    top, bottom = min(vertical_marker_rows), max(vertical_marker_rows)

    crossing = grid[strand_row][strand_col]
    horizontal_priority = crossing == horizontal_base

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(top, bottom + 1):
        horizontal_lane = (row - top) % 2 == 1
        for col in range(left, right + 1):
            vertical_lane = (col - left) % 2 == 1
            if horizontal_priority:
                if horizontal_lane:
                    value = horizontal_base
                elif vertical_lane:
                    value = vertical_base
                else:
                    value = vertical_marker
            else:
                if vertical_lane:
                    value = vertical_base
                elif horizontal_lane:
                    value = horizontal_base
                else:
                    value = vertical_marker
            output[row][col] = value
    return output
