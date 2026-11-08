from __future__ import annotations

from collections import deque


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def solve(grid):
    """Recolor centers of whole three-cell diagonal gray components."""
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    diagonal_shapes = {
        ((0, 0), (1, 1), (2, 2)),
        ((0, 2), (1, 1), (2, 0)),
    }

    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc):
                        continue
                    neighbor = (r + dr, c + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor in remaining
                    ):
                        remaining.remove(neighbor)
                        queue.append(neighbor)
                        component.append(neighbor)

        if _normalize(component) in diagonal_shapes:
            middle_r, middle_c = sorted(component)[1]
            output[middle_r][middle_c] = 4

    return output
