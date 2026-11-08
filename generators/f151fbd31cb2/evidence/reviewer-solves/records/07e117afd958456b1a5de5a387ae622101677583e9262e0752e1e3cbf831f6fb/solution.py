"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations

from copy import deepcopy

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
L_SHAPES = {
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
}
PLUS = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _green_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def solve(grid):
    """Recolor the green family selected by the shape key to the color key."""
    out = deepcopy(grid)
    shape_key = next(
        value for row in grid for value in row if value in (1, 4)
    )
    replacement = next(
        value for row in grid for value in row if value in (2, 6, 8)
    )
    selected = "L" if shape_key == 1 else "PLUS"

    for component in _green_components(grid):
        normalized = _normalize(component)
        family = "L" if normalized in L_SHAPES else "PLUS" if normalized == PLUS else "OTHER"
        if family == selected:
            for r, c in component:
                out[r][c] = replacement
    return out
