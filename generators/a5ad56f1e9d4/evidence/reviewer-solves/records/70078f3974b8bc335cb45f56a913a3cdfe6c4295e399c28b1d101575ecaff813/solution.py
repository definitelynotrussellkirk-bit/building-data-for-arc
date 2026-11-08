from __future__ import annotations


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def solve(grid):
    """Replace the gray rectangle by a Manhattan Voronoi split.

    Each non-background, non-gray singleton is projected onto the closest cell
    of the gray rectangle.  Gray cells take the color of the nearest projected
    marker; row-major marker order breaks equal-distance ties.
    """
    gray = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == 5
    ]
    if not gray:
        return [row[:] for row in grid]

    top = min(row for row, _ in gray)
    bottom = max(row for row, _ in gray)
    left = min(column for _, column in gray)
    right = max(column for _, column in gray)

    markers = [
        (row_index, column_index, value)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value not in (0, 5)
    ]
    projected = [
        (
            _clamp(row, top, bottom),
            _clamp(column, left, right),
            color,
        )
        for row, column, color in markers
    ]

    result = [row[:] for row in grid]
    for row, column in gray:
        _, _, color = min(
            projected,
            key=lambda marker: abs(row - marker[0]) + abs(column - marker[1]),
        )
        result[row][column] = color
    return result
