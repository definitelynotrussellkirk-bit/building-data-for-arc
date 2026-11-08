"""Visible-example solution for ae7376fe4957."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Translate payload from the unique blue marker to the first red marker."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])

    sources = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    reds = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if len(sources) != 1 or not reds:
        raise ValueError("expected one blue source and at least one red marker")

    source = sources[0]
    target = reds[0]  # row-major order from the scan above
    delta_row = target[0] - source[0]
    delta_col = target[1] - source[1]

    shifted: list[tuple[int, int, int]] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 or (row, col) in (source, target):
                continue
            out_row = row + delta_row
            out_col = col + delta_col
            if 0 <= out_row < height and 0 <= out_col < width:
                shifted.append((out_row, out_col, value))

    if not shifted:
        return []
    top = min(row for row, _, _ in shifted)
    bottom = max(row for row, _, _ in shifted)
    left = min(col for _, col, _ in shifted)
    right = max(col for _, col, _ in shifted)
    output = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for row, col, value in shifted:
        output[row - top][col - left] = value
    return output
