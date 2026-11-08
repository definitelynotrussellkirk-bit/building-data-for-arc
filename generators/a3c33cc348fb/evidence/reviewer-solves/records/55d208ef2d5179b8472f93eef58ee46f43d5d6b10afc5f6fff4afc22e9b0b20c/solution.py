"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand the framed rectangle's bounding box to consume the cyan marker."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    cyan = next(
        (
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 8
        ),
        None,
    )
    if cyan is None:
        raise ValueError("expected one cyan marker")

    cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 8)
    ]
    if not cells:
        raise ValueError("expected a non-background rectangle")

    rows = [row for row, _, _ in cells]
    cols = [col for _, col, _ in cells]
    row0, row1 = min(rows), max(rows)
    col0, col1 = min(cols), max(cols)
    frame_color = grid[row0][col0]
    inner_color = next(
        (value for _, _, value in cells if value != frame_color),
        frame_color,
    )

    cyan_row, cyan_col = cyan
    new_row0, new_row1 = min(row0, cyan_row), max(row1, cyan_row)
    new_col0, new_col1 = min(col0, cyan_col), max(col1, cyan_col)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(new_row0, new_row1 + 1):
        for col in range(new_col0, new_col1 + 1):
            on_perimeter = (
                row in (new_row0, new_row1)
                or col in (new_col0, new_col1)
            )
            output[row][col] = frame_color if on_perimeter else inner_color
    return output
