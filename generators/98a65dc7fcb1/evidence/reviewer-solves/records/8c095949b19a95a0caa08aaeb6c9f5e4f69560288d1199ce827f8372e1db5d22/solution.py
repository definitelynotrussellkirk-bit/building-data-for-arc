"""Reviewer-authored solution based on this episode's visible examples.

Earlier exposure to the task rule was declared. No reference was opened in
this solve phase. This program does not import any generator or reference.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(row, list) or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid)):
        raise ValueError('expected a nonempty rectangular integer color grid')
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            color = grid[row - 1][col - 1]
            if color != 0 and all(
                grid[row + dr][col + dc] == color
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr != 0 or dc != 0
            ):
                output[row][col] = color
    return output
