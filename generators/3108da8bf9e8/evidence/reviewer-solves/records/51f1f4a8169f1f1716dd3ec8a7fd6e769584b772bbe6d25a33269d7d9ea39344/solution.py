"""Visible-example solution for the reviewer solve episode."""

from __future__ import annotations


def solve(grid):
    """Sort the nine 3x3 blocks by their number of color-1 cells."""
    origins = [(br * 4, bc * 4) for br in range(3) for bc in range(3)]
    blocks = []
    for top, left in origins:
        block = [row[left : left + 3] for row in grid[top : top + 3]]
        one_count = sum(value == 1 for row in block for value in row)
        blocks.append((one_count, block))

    blocks.sort(key=lambda item: item[0])
    destinations = [
        (2, 0), (2, 1), (2, 2),
        (1, 0), (1, 1), (1, 2),
        (0, 0), (0, 1), (0, 2),
    ]
    output = [[0 for _ in range(11)] for _ in range(11)]
    for (_, block), (br, bc) in zip(blocks, destinations):
        top, left = br * 4, bc * 4
        for dr in range(3):
            for dc in range(3):
                output[top + dr][left + dc] = block[dr][dc]
    return output
