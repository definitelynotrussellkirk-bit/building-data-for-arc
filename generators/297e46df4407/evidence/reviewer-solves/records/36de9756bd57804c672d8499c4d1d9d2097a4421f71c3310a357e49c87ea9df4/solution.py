from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay a translated color-8 copy of the color-1 shape.

    The translation is the displacement from the unique color-2 marker to
    the unique color-3 marker.  Existing cells are otherwise preserved;
    translated cells overwrite whatever lies at their destinations.
    """
    result = [row[:] for row in grid]
    ones: list[tuple[int, int]] = []
    marker_2: tuple[int, int] | None = None
    marker_3: tuple[int, int] | None = None

    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 1:
                ones.append((row_index, column_index))
            elif value == 2:
                marker_2 = (row_index, column_index)
            elif value == 3:
                marker_3 = (row_index, column_index)

    if marker_2 is None or marker_3 is None:
        return result

    row_shift = marker_3[0] - marker_2[0]
    column_shift = marker_3[1] - marker_2[1]
    height = len(result)

    for row_index, column_index in ones:
        target_row = row_index + row_shift
        target_column = column_index + column_shift
        if 0 <= target_row < height and 0 <= target_column < len(result[target_row]):
            result[target_row][target_column] = 8

    return result
