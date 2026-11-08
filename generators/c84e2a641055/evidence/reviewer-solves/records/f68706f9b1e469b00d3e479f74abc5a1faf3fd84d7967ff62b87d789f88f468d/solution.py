from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Move the complete nonzero pattern down until its lowest row is the floor."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    cells = [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return [list(row) for row in grid]

    shift = height - 1 - max(row for row, _column, _value in cells)
    output = [[0] * width for _ in range(height)]
    for row, column, value in cells:
        output[row + shift][column] = value
    return output
