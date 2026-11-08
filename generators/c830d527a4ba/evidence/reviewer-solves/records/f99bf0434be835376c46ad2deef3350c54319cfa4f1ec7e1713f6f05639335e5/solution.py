"""Visible-example solution for the exposed c830d527a4ba solve episode."""
from __future__ import annotations


def _crop_color(grid: list[list[int]], color: int) -> list[list[int]]:
    cells = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == color
    ]
    if not cells:
        raise ValueError(f"color {color} is absent")
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    bottom = max(row for row, _ in cells)
    right = max(col for _, col in cells)
    return [
        [1 if grid[row][col] == color else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def _crop_codes(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value in (2, 3, 4, 5)
    ]
    if not cells:
        raise ValueError("code grid is absent")
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    bottom = max(row for row, _ in cells)
    right = max(col for _, col in cells)
    return [line[left : right + 1] for line in grid[top : bottom + 1]]


def _rotate_cw(tile: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*tile[::-1])]


def _transform(template: list[list[int]], code: int) -> list[list[int]]:
    if code == 0:
        return [[0 for _ in row] for row in template]
    if code == 2:
        shape = [row[:] for row in template]
    elif code == 3:
        shape = _rotate_cw(template)
    elif code == 4:
        shape = [row[::-1] for row in template[::-1]]
    elif code == 5:
        shape = [row[::-1] for row in template]
    else:
        raise ValueError(f"unexpected code {code}")
    return [[code if value else 0 for value in row] for row in shape]


def solve(grid: list[list[int]]) -> list[list[int]]:
    template = _crop_color(grid, 1)
    codes = _crop_codes(grid)

    rendered_rows: list[list[list[int]]] = []
    widths: list[int] = []
    for code_row in codes:
        tiles = [_transform(template, code) for code in code_row]
        row_height = max(len(tile) for tile in tiles)
        row_width = sum(len(tile[0]) for tile in tiles) + len(tiles) - 1
        strip = [[0] * row_width for _ in range(row_height)]
        cursor = 0
        for tile in tiles:
            top = (row_height - len(tile)) // 2
            for r, line in enumerate(tile):
                strip[top + r][cursor : cursor + len(line)] = line
            cursor += len(tile[0]) + 1
        rendered_rows.append(strip)
        widths.append(row_width)

    output_height = sum(len(strip) for strip in rendered_rows) + len(rendered_rows) - 1
    output_width = max(widths)
    output = [[0] * output_width for _ in range(output_height)]
    cursor = 0
    for strip, strip_width in zip(rendered_rows, widths):
        left = (output_width - strip_width) // 2
        for r, line in enumerate(strip):
            output[cursor + r][left : left + strip_width] = line
        cursor += len(strip) + 1
    return output
