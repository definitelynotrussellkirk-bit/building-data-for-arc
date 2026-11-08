"""Visible-example solution for review task 86af5978a32a."""
from __future__ import annotations


def _split(grid):
    h = len(grid)
    w = len(grid[0])
    if w == 2 * h:
        k = h
        first = [row[:k] for row in grid]
        second = [row[k:] for row in grid]
    elif h == 2 * w:
        k = w
        first = [list(row) for row in grid[:k]]
        second = [list(row) for row in grid[k:]]
    else:
        raise ValueError("expected two equal square panels")
    return k, first, second


def _colors(panel):
    return {value for row in panel for value in row if value != 0}


def solve(grid):
    """Use the multicolor panel as a layout and the one-color panel as a mask."""
    k, first, second = _split(grid)
    first_colors = _colors(first)
    second_colors = _colors(second)
    if len(first_colors) > len(second_colors):
        layout, shape = first, second
    elif len(second_colors) > len(first_colors):
        layout, shape = second, first
    else:
        raise ValueError("panel roles are ambiguous")

    mask = [
        (row, col)
        for row in range(k)
        for col in range(k)
        if shape[row][col] != 0
    ]
    output = [[0 for _ in range(k * k)] for _ in range(k * k)]
    for layout_row in range(k):
        for layout_col in range(k):
            color = layout[layout_row][layout_col]
            if color == 0:
                continue
            for shape_row, shape_col in mask:
                output[layout_row * k + shape_row][layout_col * k + shape_col] = color
    return output
