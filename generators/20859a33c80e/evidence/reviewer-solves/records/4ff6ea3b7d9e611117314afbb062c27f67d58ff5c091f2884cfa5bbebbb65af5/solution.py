from collections import deque


def _components(grid):
    """Return monochromatic 4-connected non-background components."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    parts = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            parts.append(
                {
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return parts


def _strictly_larger_box(outer, inner):
    or0, oc0, or1, oc1 = outer
    ir0, ic0, ir1, ic1 = inner
    return (
        or0 <= ir0
        and oc0 <= ic0
        and or1 >= ir1
        and oc1 >= ic1
        and outer != inner
    )


def solve(grid):
    """Recolor every object by its rectangular containment depth.

    The outside objects receive color 2.  Every enclosing component adds one,
    so objects inside one frame receive 3, objects inside two nested frames
    receive 4, and so on.  Background cells remain zero.
    """
    parts = _components(grid)
    result = [row[:] for row in grid]

    for part in parts:
        depth = sum(
            _strictly_larger_box(other["bbox"], part["bbox"])
            for other in parts
            if other is not part
        )
        color = 2 + depth
        for r, c in part["cells"]:
            result[r][c] = color

    return result
