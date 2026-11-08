"""Count monochromatic cardinal-neighbor regions and draw three bars.

Written for this episode from its visible examples. No repository imports,
reference calls, stored examples, task IDs, or generator-specific positions.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError('expected a nonempty grid')
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError('expected integer colors 0..9')
    counts = []
    for color in (1, 2, 3):
        remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
        number = 0
        while remaining:
            start = remaining.pop()
            number += 1
            stack = [start]
            while stack:
                r, c = stack.pop()
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        counts.append(number)
    out_width = max(1, *counts)
    return [[color if col < count else 0 for col in range(out_width)]
            for color, count in zip((1, 2, 3), counts)]
