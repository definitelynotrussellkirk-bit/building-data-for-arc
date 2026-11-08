"""Standalone candidate inferred from this episode's visible demonstrations.

Earlier rule exposure during the review is declared in SOLVE_NOTES.md. This
module neither imports repository code nor reads any files or private answers.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolour separate objects according to their ascending occupied area."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer colours 0..9")
    h, w = len(grid), len(grid[0])
    visited: set[tuple[int, int]] = set()
    objects: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in visited:
                continue
            stack = [(r, c)]
            visited.add((r, c))
            cells = []
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                    if (0 <= yy < h and 0 <= xx < w and grid[yy][xx] != 0
                            and (yy, xx) not in visited):
                        visited.add((yy, xx))
                        stack.append((yy, xx))
            objects.append(cells)
    if len(objects) not in (2, 3):
        raise ValueError("visible rule supports two or three separate objects")
    if len({len(cells) for cells in objects}) != len(objects):
        raise ValueError("visible demonstrations do not specify tied areas")
    result = [[0] * w for _ in range(h)]
    for colour, cells in enumerate(sorted(objects, key=len), start=2):
        for r, c in cells:
            result[r][c] = colour
    return result
