"""Visible-example solution for task 5751ed9bdf85."""
from __future__ import annotations


def _gray_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    component.append(neighbor)
        components.append(component)
    return components


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the unique gray frame containing exactly one colored marker."""
    output = [row[:] for row in grid]
    for component in _gray_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        row0, row1 = min(rows), max(rows)
        col0, col1 = min(cols), max(cols)
        markers = [
            grid[row][col]
            for row in range(row0 + 1, row1)
            for col in range(col0 + 1, col1)
            if grid[row][col] not in (0, 5)
        ]
        if len(markers) != 1:
            continue
        marker = markers[0]
        for row in range(row0 + 1, row1):
            for col in range(col0 + 1, col1):
                if output[row][col] == 0:
                    output[row][col] = marker
        return output
    return output
