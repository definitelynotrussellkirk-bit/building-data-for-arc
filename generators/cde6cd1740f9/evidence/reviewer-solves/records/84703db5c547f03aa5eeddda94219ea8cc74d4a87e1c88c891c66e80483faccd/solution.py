"""Visible-example solution for ARC task cde6cd1740f9."""
from __future__ import annotations

from collections import Counter
from math import isqrt


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    result = [[0] * width for _ in range(height)]

    for column in range(width):
        source = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        if not source:
            continue

        side = isqrt(len(source))
        if side * side != len(source):
            raise ValueError("each active column must contain a square number of cells")

        bottom_up = list(reversed(source))
        counts = Counter(bottom_up)
        color_order = []
        for color in bottom_up:
            if color not in color_order:
                color_order.append(color)

        color_index = 0
        remaining = counts[color_order[0]]
        for level in range(side):
            layer_width = 2 * side - 1 - 2 * level
            if remaining == 0:
                color_index += 1
                remaining = counts[color_order[color_index]]
            if remaining < layer_width:
                raise ValueError("a color count does not fill complete pyramid layers")

            color = color_order[color_index]
            row = height - 1 - level
            left = column - layer_width // 2
            right = column + layer_width // 2
            if left < 0 or right >= width:
                raise ValueError("pyramid would leave the canvas")
            for out_column in range(left, right + 1):
                result[row][out_column] = color
            remaining -= layer_width

        if remaining != 0 or color_index != len(color_order) - 1:
            raise ValueError("unused source colors remain")

    return result
