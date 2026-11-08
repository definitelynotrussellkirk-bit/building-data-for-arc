from __future__ import annotations


def _tight_mask(grid: list[list[int]], color: int) -> list[list[bool]]:
    cells = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == color
    ]
    if not cells:
        raise ValueError(f"missing color {color}")

    row_min = min(row for row, _ in cells)
    row_max = max(row for row, _ in cells)
    column_min = min(column for _, column in cells)
    column_max = max(column for _, column in cells)
    return [
        [grid[row][column] == color for column in range(column_min, column_max + 1)]
        for row in range(row_min, row_max + 1)
    ]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Return the tight-cropped XOR of the red and green object silhouettes."""
    red = _tight_mask(grid, 2)
    green = _tight_mask(grid, 3)

    height = max(len(red), len(green))
    width = max(len(red[0]), len(green[0]))
    difference = [
        [
            (
                row < len(red)
                and column < len(red[0])
                and red[row][column]
            )
            != (
                row < len(green)
                and column < len(green[0])
                and green[row][column]
            )
            for column in range(width)
        ]
        for row in range(height)
    ]

    occupied = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if difference[row][column]
    ]
    if not occupied:
        return [[0]]

    row_min = min(row for row, _ in occupied)
    row_max = max(row for row, _ in occupied)
    column_min = min(column for _, column in occupied)
    column_max = max(column for _, column in occupied)
    return [
        [8 if difference[row][column] else 0 for column in range(column_min, column_max + 1)]
        for row in range(row_min, row_max + 1)
    ]
