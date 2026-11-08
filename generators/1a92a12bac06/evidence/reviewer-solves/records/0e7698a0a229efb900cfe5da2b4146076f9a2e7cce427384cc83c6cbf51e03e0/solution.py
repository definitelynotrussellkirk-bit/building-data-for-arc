"""Visible-example solve for reviewer task 1a92a12bac06."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    """Recolor the lower floor(height/2) cells of each red component cyan."""
    if not grid or not grid[0]:
        return deepcopy(grid)

    output = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }

    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)

        rows = [row for row, _ in component]
        bottom = max(rows)
        component_height = bottom - min(rows) + 1
        cyan_start = bottom - component_height // 2 + 1
        for row, col in component:
            if row >= cyan_start:
                output[row][col] = 8

    return output
