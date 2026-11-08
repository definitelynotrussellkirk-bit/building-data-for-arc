"""Visible-example solution for task 59ccf6f5cc65."""
from __future__ import annotations


def solve(grid):
    """Recolor each 4-connected orange component that includes an exact corner."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    }
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    while unseen:
        start = unseen.pop()
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
        if component & corners:
            for row, col in component:
                out[row][col] = 1
    return out
