"""Repack each occupied input column into a bottom-aligned pyramid."""

from math import isqrt


def solve(grid):
    height = len(grid)
    if not height:
        return []
    width = len(grid[0])
    out = [[0] * width for _ in range(height)]

    for center in range(width):
        colors = [grid[row][center] for row in range(height) if grid[row][center] != 0]
        if not colors:
            continue
        levels = isqrt(len(colors))
        if levels * levels != len(colors):
            raise ValueError("The observed pyramid rule requires a square cell count per column")

        index = 0
        for level in range(levels):
            row = height - levels + level
            for column in range(center - level, center + level + 1):
                out[row][column] = colors[index]
                index += 1

    return out
