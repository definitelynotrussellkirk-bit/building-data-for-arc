"""Visible-example solution for review task 28e5fbc279ab."""
from __future__ import annotations


def _components_of_color(grid, color):
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        components.append(cells)
    return components


def solve(grid):
    """Stamp the largest connected green shape at every colored singleton."""
    out = [list(row) for row in grid]
    green_components = _components_of_color(grid, 3)
    if not green_components:
        return out

    reference = max(green_components, key=lambda cells: (len(cells), -min(cells)[0], -min(cells)[1]))
    top = min(r for r, _ in reference)
    left = min(c for _, c in reference)
    offsets = [(r - top, c - left) for r, c in reference]

    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 3)
    ]
    for r, c, color in markers:
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = color
    return out
