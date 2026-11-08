"""Visible-example solution for the reviewer solve episode."""
from copy import deepcopy


def _components_of_six(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        components.append(cells)
    return components


def solve(grid):
    """Fill the interior of every hollow color-6 rectangle with color 8."""
    out = deepcopy(grid)
    for cells in _components_of_six(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if cells != border:
            continue
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 8
    return out
