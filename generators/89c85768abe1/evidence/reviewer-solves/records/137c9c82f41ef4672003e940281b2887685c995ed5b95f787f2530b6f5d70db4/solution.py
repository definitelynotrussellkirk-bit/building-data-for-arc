from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the inclusive bounding box of each nonzero color pair."""
    out = [row[:] for row in grid]
    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, col_index))

    for color, cells in positions.items():
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                out[row][col] = color
    return out
