"""Visible-example solution for blind task bbbabb45042b."""

from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    """Return 4-connected components of ``cells`` in deterministic order."""
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def solve(grid: Grid) -> Grid:
    """Stamp the largest blue component, normalized at each red marker.

    The red marker itself is the top-left anchor and remains red, so it also
    supplies the top-left stencil cell when the blue component lacks one.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]

    blue = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    red_anchors = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )
    if not blue:
        return output

    components = _components(blue)
    template = max(components, key=lambda component: (len(component), -min(component)[0], -min(component)[1]))
    min_row = min(row for row, _ in template)
    min_col = min(col for _, col in template)
    offsets = {(0, 0)} | {(row - min_row, col - min_col) for row, col in template}

    for anchor_row, anchor_col in red_anchors:
        for delta_row, delta_col in offsets:
            row = anchor_row + delta_row
            col = anchor_col + delta_col
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = 1

    return output
