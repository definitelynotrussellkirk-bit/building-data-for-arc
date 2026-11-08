"""Visible-example solution for 4c93dc1552b3."""
from __future__ import annotations


def solve(grid):
    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }

    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    component.append(neighbor)

        row0 = min(row for row, _ in component)
        row1 = max(row for row, _ in component)
        col0 = min(col for _, col in component)
        col1 = max(col for _, col in component)
        box_height = row1 - row0 + 1
        box_width = col1 - col0 + 1
        is_solid_rectangle = (
            box_height >= 2
            and box_width >= 2
            and len(component) == box_height * box_width
        )
        if is_solid_rectangle:
            for row, col in (
                (row0, col0),
                (row0, col1),
                (row1, col0),
                (row1, col1),
            ):
                output[row][col] = 2

    return output
