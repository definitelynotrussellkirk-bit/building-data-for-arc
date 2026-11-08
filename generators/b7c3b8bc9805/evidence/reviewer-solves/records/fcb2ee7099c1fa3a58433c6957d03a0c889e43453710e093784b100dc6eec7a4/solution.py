from __future__ import annotations


def solve(grid):
    """Fill the gray frame interior with the marker-phase checkerboard."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    gray = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 5
    ]
    if not gray:
        raise ValueError("missing gray frame")

    frame_top = min(row for row, _ in gray)
    frame_bottom = max(row for row, _ in gray)
    frame_left = min(column for _, column in gray)
    frame_right = max(column for _, column in gray)

    markers = sorted(
        (row, column, grid[row][column])
        for row in range(height)
        for column in range(width)
        if grid[row][column] not in (0, 5)
    )
    if len(markers) != 2:
        raise ValueError("expected exactly two non-gray markers")
    first, second = markers

    frame_center_row = (frame_top + frame_bottom) // 2
    frame_center_column = (frame_left + frame_right) // 2
    first_row_side = 0 if first[0] < frame_center_row else 1
    first_column_side = 0 if first[1] < frame_center_column else 1
    first_phase = (first_row_side + first_column_side) % 2

    inner_top = frame_top + 1
    inner_bottom = frame_bottom - 1
    inner_left = frame_left + 1
    inner_right = frame_right - 1
    row_midpoint = (inner_top + inner_bottom) // 2
    column_midpoint = (inner_left + inner_right) // 2

    result = [row[:] for row in grid]
    for row in range(inner_top, inner_bottom + 1):
        row_side = 0 if row <= row_midpoint else 1
        for column in range(inner_left, inner_right + 1):
            column_side = 0 if column <= column_midpoint else 1
            phase = (row_side + column_side) % 2
            result[row][column] = first[2] if phase == first_phase else second[2]
    return result
