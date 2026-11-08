"""Visible-example solution for the prepared ARC episode."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replicate the nonzero/non-marker template at each 9 marker."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    template_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]
    if not template_cells:
        return output

    source_row = min(row for row, _, _ in template_cells)
    source_col = min(col for _, col, _ in template_cells)
    template = [
        (row - source_row, col - source_col, value)
        for row, col, value in template_cells
    ]
    anchors = [(source_row, source_col)] + [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]

    for anchor_row, anchor_col in anchors:
        for row_offset, col_offset, value in template:
            row = anchor_row + row_offset
            col = anchor_col + col_offset
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = value

    return output


# Common aliases used by ARC harnesses.
transform = solve
apply = solve
