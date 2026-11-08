"""Visible-example solver for the reviewer-authored ARC episode."""

from __future__ import annotations

from collections.abc import Sequence

Grid = list[list[int]]


def _copy_rectangular_grid(grid: Sequence[Sequence[int]]) -> Grid:
    if not grid:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be a non-empty rectangle")
    return [list(row) for row in grid]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Expand diagonal rays selected by the color-2 cells of a 2x2 motif.

    The nonzero motif is a 2x2 block.  Its non-2 color is the paint color.
    Each color-2 corner activates the outward diagonal associated with that
    corner.  The whole motif is first recolored, then every motif cell emits
    a ray in every active direction until the grid boundary.
    """

    output = _copy_rectangular_grid(grid)
    height, width = len(output), len(output[0])

    occupied = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if output[row][col] != 0
    ]
    if not occupied:
        return output

    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    if (bottom - top, right - left) != (1, 1):
        raise ValueError("expected the nonzero motif to occupy one 2x2 block")

    motif_cells = [
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    ]
    if any(output[row][col] == 0 for row, col in motif_cells):
        raise ValueError("expected all four cells of the 2x2 motif to be nonzero")

    paint_colors = {
        output[row][col]
        for row, col in motif_cells
        if output[row][col] != 2
    }
    if len(paint_colors) != 1:
        raise ValueError("expected exactly one non-2 motif color")
    paint = paint_colors.pop()

    directions: set[tuple[int, int]] = set()
    for row, col in motif_cells:
        if output[row][col] == 2:
            directions.add(
                (-1 if row == top else 1, -1 if col == left else 1)
            )

    for row, col in motif_cells:
        output[row][col] = paint

    for delta_row, delta_col in directions:
        for start_row, start_col in motif_cells:
            row = start_row + delta_row
            col = start_col + delta_col
            while 0 <= row < height and 0 <= col < width:
                output[row][col] = paint
                row += delta_row
                col += delta_col

    return output
