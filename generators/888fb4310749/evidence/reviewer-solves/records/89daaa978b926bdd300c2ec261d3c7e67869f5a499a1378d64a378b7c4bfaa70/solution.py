"""Visible-example solution for ARC task 888fb4310749."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    nonzero = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not nonzero:
        return [row[:] for row in grid]

    row0 = min(row for row, _ in nonzero)
    row1 = max(row for row, _ in nonzero)
    col0 = min(col for _, col in nonzero)
    col1 = max(col for _, col in nonzero)
    block_height = row1 - row0 + 1
    block_width = col1 - col0 + 1
    color = grid[row0][col0]
    alternate = 9 - color
    period = block_height + block_width

    output = [row[:] for row in grid]

    def intersects(top, left, stamp_height, stamp_width):
        return (
            top < height
            and left < width
            and top + stamp_height > 0
            and left + stamp_width > 0
        )

    def stamp(top, left, stamp_height, stamp_width, stamp_color):
        for row in range(top, top + stamp_height):
            if not 0 <= row < height:
                continue
            for col in range(left, left + stamp_width):
                if 0 <= col < width:
                    output[row][col] = stamp_color

    # Paint the quarter-turned companion rectangles first.
    limit = 2 + (height + width) // max(1, period)
    for multiple in range(-limit, limit + 1):
        diagonal_row = row0 + multiple * period
        for sign in (1, -1):
            diagonal_col = col0 + sign * multiple * period
            turned_row = diagonal_row + block_height
            turned_col = diagonal_col + (
                block_width if sign == 1 else -block_height
            )
            if intersects(
                turned_row,
                turned_col,
                block_width,
                block_height,
            ):
                stamp(
                    turned_row,
                    turned_col,
                    block_width,
                    block_height,
                    alternate,
                )

    # Repaint the original-orientation diagonal blocks last.
    anchors = set()
    for multiple in range(-limit, limit + 1):
        diagonal_row = row0 + multiple * period
        for sign in (1, -1):
            diagonal_col = col0 + sign * multiple * period
            anchor = (diagonal_row, diagonal_col)
            if anchor in anchors:
                continue
            if intersects(
                diagonal_row,
                diagonal_col,
                block_height,
                block_width,
            ):
                anchors.add(anchor)
                stamp(
                    diagonal_row,
                    diagonal_col,
                    block_height,
                    block_width,
                    color,
                )

    return output
