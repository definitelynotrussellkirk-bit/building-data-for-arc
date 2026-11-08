"""Visible-example solution for the exposed 083ba0fc4534 solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(dividers) != 2:
        raise ValueError("expected exactly two full-height color-5 dividers")
    first, second = dividers
    panel_w = first
    if second != 2 * panel_w + 1 or width != 3 * panel_w + 2:
        raise ValueError("dividers do not delimit three equal-width panels")

    output = [[0] * panel_w for _ in range(height)]
    for row in range(height):
        for col in range(panel_w):
            values = (
                grid[row][col],
                grid[row][first + 1 + col],
                grid[row][second + 1 + col],
            )
            for value in values:
                if value != 0 and values.count(value) >= 2:
                    output[row][col] = value
                    break
    return output
