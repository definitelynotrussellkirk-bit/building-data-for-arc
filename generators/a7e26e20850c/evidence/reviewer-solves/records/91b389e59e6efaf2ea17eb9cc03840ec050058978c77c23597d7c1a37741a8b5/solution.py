"""Visible-example solution for a7e26e20850c."""
from __future__ import annotations

from copy import deepcopy


def _legend(row: list[int]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    col = 0
    while col < len(row):
        color = row[col]
        if color == 0:
            col += 1
            continue
        start = col
        while col < len(row) and row[col] == color:
            col += 1
        size = col - start
        if size in mapping and mapping[size] != color:
            raise ValueError(f"ambiguous legend for size {size}")
        mapping[size] = color
    return mapping


def _gray_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if r > 0 and value == 5
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor each gray object using the top-row run of matching length."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    mapping = _legend(grid[0])
    out = deepcopy(grid)
    for component in _gray_components(grid):
        size = len(component)
        if size not in mapping:
            raise ValueError(f"gray object size {size} is missing from the legend")
        color = mapping[size]
        for r, c in component:
            out[r][c] = color
    return out
