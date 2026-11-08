from __future__ import annotations


def solve(grid):
    """Reflect colored cells left of the full-height gray divider to its right."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a non-empty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    divider_columns = [
        col
        for col in range(width)
        if all(row[col] == 5 for row in grid)
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected exactly one full-height gray divider")
    divider = divider_columns[0]

    output = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        for col in range(divider):
            value = row[col]
            if value in (0, 5):
                continue
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < width:
                output[row_index][mirror_col] = value
    return output
