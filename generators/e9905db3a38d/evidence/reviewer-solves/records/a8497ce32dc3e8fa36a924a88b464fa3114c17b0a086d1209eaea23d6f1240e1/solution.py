from __future__ import annotations

from typing import Iterable

Point = tuple[int, int]
Grid = list[list[int]]


def _crop_color(grid: Grid, color: int) -> Grid:
    points: list[Point] = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == color
    ]
    if not points:
        raise ValueError(f"missing template color {color}")
    row0 = min(row for row, _ in points)
    row1 = max(row for row, _ in points)
    col0 = min(col for _, col in points)
    col1 = max(col for _, col in points)
    return [
        [color if grid[row][col] == color else 0 for col in range(col0, col1 + 1)]
        for row in range(row0, row1 + 1)
    ]


def _rotate_cw(tile: Grid) -> Grid:
    return [list(row) for row in zip(*tile[::-1])]


def _paste(output: Grid, tile: Grid, top: int, left: int) -> None:
    for row, line in enumerate(tile):
        for col, value in enumerate(line):
            if value != 0:
                output[top + row][left + col] = value


def solve(grid: Grid) -> Grid:
    if len(grid) < 3 or not grid or not grid[0]:
        raise ValueError("expected a non-empty grid with two code rows")

    top = grid[:-2]
    codes = grid[-2:]
    template_1 = _crop_color(top, 1)
    template_2 = _crop_color(top, 2)
    tile_height = len(template_1)
    tile_width = len(template_1[0])

    active_columns = [
        col
        for col in range(len(grid[0]))
        if codes[0][col] != 0 or codes[1][col] != 0
    ]
    if not active_columns:
        return [[0]]
    first, last = min(active_columns), max(active_columns)
    code_width = last - first + 1

    output = [
        [0 for _ in range(code_width * tile_width + code_width - 1)]
        for _ in range(2 * tile_height + 1)
    ]
    decoded = {
        1: template_1,
        2: template_2,
        3: _rotate_cw(template_1),
        4: _rotate_cw(template_2),
    }
    for code_row in range(2):
        for local_col, source_col in enumerate(range(first, last + 1)):
            code = codes[code_row][source_col]
            tile = decoded.get(code)
            if tile is not None:
                _paste(
                    output,
                    tile,
                    code_row * (tile_height + 1),
                    local_col * (tile_width + 1),
                )
    return output
