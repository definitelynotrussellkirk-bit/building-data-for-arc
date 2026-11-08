from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill blank horizontal bridges for colors occurring exactly twice globally."""
    out = [row[:] for row in grid]
    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (row_a, col_a), (row_b, col_b) = cells
        if row_a != row_b:
            continue
        left, right = sorted((col_a, col_b))
        if not all(grid[row_a][column] == 0 for column in range(left + 1, right)):
            continue
        for column in range(left, right + 1):
            out[row_a][column] = color
    return out
