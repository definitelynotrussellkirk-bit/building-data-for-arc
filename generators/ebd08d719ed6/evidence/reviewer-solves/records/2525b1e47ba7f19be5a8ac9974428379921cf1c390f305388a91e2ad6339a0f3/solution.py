"""Visible-example solution for the selected ARC task."""
from __future__ import annotations


def _segments(size: int, dividers: list[int]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    previous = -1
    for divider in dividers + [size]:
        if divider > previous + 1:
            result.append((previous + 1, divider))
        previous = divider
    return result


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor the occupied cells of the uniquely densest divider tile to 8."""
    height = len(grid)
    width = len(grid[0])
    divider_rows = [
        row for row in range(height) if all(grid[row][col] == 9 for col in range(width))
    ]
    divider_cols = [
        col for col in range(width) if all(grid[row][col] == 9 for row in range(height))
    ]
    row_segments = _segments(height, divider_rows)
    col_segments = _segments(width, divider_cols)

    tiles: list[list[tuple[int, int]]] = []
    counts: list[int] = []
    for row_start, row_end in row_segments:
        for col_start, col_end in col_segments:
            cells = [
                (row, col)
                for row in range(row_start, row_end)
                for col in range(col_start, col_end)
            ]
            tiles.append(cells)
            counts.append(sum(grid[row][col] != 0 for row, col in cells))

    target = max(range(len(tiles)), key=counts.__getitem__)
    output = [row[:] for row in grid]
    for row, col in tiles[target]:
        if output[row][col] != 0:
            output[row][col] = 8
    return output
