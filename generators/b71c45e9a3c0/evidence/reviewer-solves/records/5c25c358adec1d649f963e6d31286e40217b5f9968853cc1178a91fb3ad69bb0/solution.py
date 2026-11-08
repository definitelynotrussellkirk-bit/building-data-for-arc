"""Visible-example solution for the generated b71c45e9a3c0 episode."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 3
    }

    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)

        top = min(row for row, _ in component)
        left = min(col for _, col in component)
        key_color = grid[top - 1][left]
        for row, col in component:
            out[row][col] = key_color

    return out
