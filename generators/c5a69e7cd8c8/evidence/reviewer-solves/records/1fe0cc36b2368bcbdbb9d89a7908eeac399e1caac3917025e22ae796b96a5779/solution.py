"""Visible-example solution for the prepared reviewer solve episode."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend the singleton marker away from the surrounding support object.

    The nonzero color occurring once is the marker.  Exactly one cardinal side
    of that marker is open (background); the support occupies the other sides.
    On the ray opposite the opening, preserve the support and recolor every
    background cell beyond it with the marker color.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    counts: dict[int, int] = {}
    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color == 0:
                continue
            counts[color] = counts.get(color, 0) + 1
            positions.setdefault(color, []).append((row_index, column_index))

    singleton_colors = [color for color, count in counts.items() if count == 1]
    if len(singleton_colors) != 1:
        raise ValueError("expected exactly one singleton nonzero color")

    marker_color = singleton_colors[0]
    marker_row, marker_column = positions[marker_color][0]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    open_directions: list[tuple[int, int]] = []
    for delta_row, delta_column in directions:
        row = marker_row + delta_row
        column = marker_column + delta_column
        if not (0 <= row < height and 0 <= column < width) or grid[row][column] == 0:
            open_directions.append((delta_row, delta_column))

    if len(open_directions) != 1:
        raise ValueError("expected exactly one open cardinal side at the marker")

    open_row, open_column = open_directions[0]
    ray_row, ray_column = -open_row, -open_column
    result = [row[:] for row in grid]

    row = marker_row + ray_row
    column = marker_column + ray_column
    while 0 <= row < height and 0 <= column < width:
        if result[row][column] == 0:
            result[row][column] = marker_color
        row += ray_row
        column += ray_column

    return result
