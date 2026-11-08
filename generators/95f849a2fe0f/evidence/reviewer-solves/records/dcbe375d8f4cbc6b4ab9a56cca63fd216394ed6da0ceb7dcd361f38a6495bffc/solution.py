from __future__ import annotations


def _normalized_shape(grid: list[list[int]], color: int) -> tuple[set[tuple[int, int]], int, int]:
    cells = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == color
    ]
    if not cells:
        raise ValueError(f"color {color} is absent")

    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    max_column = max(column for _, column in cells)
    normalized = {(row - min_row, column - min_column) for row, column in cells}
    return normalized, max_row - min_row + 1, max_column - min_column + 1


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Top-left align the two cropped non-background shapes and return their XOR."""
    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) != 2:
        raise ValueError(f"expected exactly two non-background colors, got {colors}")

    first, first_height, first_width = _normalized_shape(grid, colors[0])
    second, second_height, second_width = _normalized_shape(grid, colors[1])
    height = max(first_height, second_height)
    width = max(first_width, second_width)

    return [
        [8 if ((row, column) in first) ^ ((row, column) in second) else 0 for column in range(width)]
        for row in range(height)
    ]
