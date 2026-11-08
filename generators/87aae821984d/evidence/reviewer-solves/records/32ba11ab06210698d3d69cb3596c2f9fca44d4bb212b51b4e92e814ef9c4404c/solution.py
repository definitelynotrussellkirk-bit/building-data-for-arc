"""Visible-example solution for ARC task 87aae821984d."""


def solve(grid):
    yellow_count = sum(value == 4 for row in grid for value in row)
    cyan = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 8
    ]
    if not cyan:
        raise ValueError("expected at least one cyan cell")

    bottom = max(row for row, _ in cyan)
    right = max(col for _, col in cyan)
    tile = [
        [8 if (bottom - 2 + row, right - 2 + col) in cyan else 0 for col in range(3)]
        for row in range(3)
    ]
    return [row * yellow_count for row in tile]
