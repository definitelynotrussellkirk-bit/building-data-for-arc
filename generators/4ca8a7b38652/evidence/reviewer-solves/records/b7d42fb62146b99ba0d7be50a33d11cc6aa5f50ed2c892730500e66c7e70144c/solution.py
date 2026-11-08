"""Enlarge pixels by the number of distinct nonzero input colors."""


def solve(grid):
    scale = len({color for row in grid for color in row if color != 0})
    return [
        [color for color in row for _ in range(scale)]
        for row in grid
        for _ in range(scale)
    ]
