"""Visible-example solution: recolor the uniquely leftmost yellow component."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    out = deepcopy(grid)
    if not grid or not grid[0]:
        return out

    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 4 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)

    if components:
        selected = min(
            components,
            key=lambda comp: (min(c for _, c in comp), min(r for r, _ in comp)),
        )
        for r, c in selected:
            out[r][c] = 3
    return out
