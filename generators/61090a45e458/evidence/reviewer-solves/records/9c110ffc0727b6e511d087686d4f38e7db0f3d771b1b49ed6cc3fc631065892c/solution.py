"""Visible-example solution for ARC task 61090a45e458.

Each monochrome rectangular frame contains two non-background interior colors:
a singleton marker and a larger object.  Recolor the larger object to the
singleton marker's color, independently inside every frame.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy


def _components(grid, color):
    """Return 4-connected components of ``color`` as sets of coordinates."""
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < height and 0 <= cc < width and (rr, cc) in remaining:
                    remaining.remove((rr, cc))
                    component.add((rr, cc))
                    queue.append((rr, cc))
        components.append(component)
    return components


def _rectangular_frames(grid):
    """Find components that are exact rectangular outlines."""
    colors = sorted({value for row in grid for value in row if value != 0})
    frames = []
    for color in colors:
        for component in _components(grid, color):
            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            if r2 - r1 < 2 or c2 - c1 < 2:
                continue
            perimeter = {
                (r, c)
                for r in range(r1, r2 + 1)
                for c in range(c1, c2 + 1)
                if r in (r1, r2) or c in (c1, c2)
            }
            if component == perimeter:
                frames.append((r1, c1, r2, c2))
    return sorted(frames)


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    output = deepcopy(grid)
    for r1, c1, r2, c2 in _rectangular_frames(grid):
        interior = [
            (r, c, grid[r][c])
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
            if grid[r][c] != 0
        ]
        counts = Counter(value for _, _, value in interior)
        singleton_colors = [color for color, count in counts.items() if count == 1]
        object_colors = [color for color, count in counts.items() if count > 1]
        if len(singleton_colors) != 1 or len(object_colors) != 1:
            continue
        marker = singleton_colors[0]
        target = object_colors[0]
        for r, c, value in interior:
            if value == target:
                output[r][c] = marker
    return output
