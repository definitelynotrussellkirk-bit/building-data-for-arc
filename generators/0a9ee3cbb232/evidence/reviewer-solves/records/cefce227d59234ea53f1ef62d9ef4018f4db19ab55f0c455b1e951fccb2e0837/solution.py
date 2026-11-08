"""Summarize the visible horizontal triples, green before red."""


def solve(grid):
    green = sum(value == 3 for row in grid for value in row) // 3
    red = sum(value == 2 for row in grid for value in row) // 3
    cells = ([3] * green + [2] * red + [0] * 6)[:6]
    return [cells[:3], cells[3:]]
