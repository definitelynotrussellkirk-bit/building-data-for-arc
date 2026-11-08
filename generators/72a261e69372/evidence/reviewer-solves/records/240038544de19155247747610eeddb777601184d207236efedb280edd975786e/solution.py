"""Visible-example solution for task 72a261e69372."""
from __future__ import annotations

from copy import deepcopy


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    comp.add(point)
                    stack.append(point)
        result.append(comp)
    return result


def _frame_box(cells):
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    if r2 - r1 < 2 or c2 - c1 < 2:
        return None
    perimeter = (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )
    return (r1, c1, r2, c2) if cells == perimeter else None


def solve(grid):
    """Recolor each 1 by its smallest intact enclosing rectangular frame."""
    out = deepcopy(grid)
    frames = []
    for color in sorted({cell for row in grid for cell in row} - {0, 1}):
        for component in _components(grid, color):
            box = _frame_box(component)
            if box is not None:
                frames.append((color, box))

    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell != 1:
                continue
            enclosing = [
                (color, box)
                for color, box in frames
                if box[0] < r < box[2] and box[1] < c < box[3]
            ]
            if enclosing:
                color, _ = min(
                    enclosing,
                    key=lambda item: (item[1][2] - item[1][0] + 1)
                    * (item[1][3] - item[1][1] + 1),
                )
                out[r][c] = color
    return out
