"""Visible-example solution for blind task f7660051ec70."""

from collections import deque
from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Fill the interior of every blue frame that contains a red marker.

    Blue (1) rectangular outlines are treated as separate objects.  If a frame's
    strict interior contains at least one red (2) cell, every zero in that
    interior becomes green (3).  The frame, red cells, and all other cells are
    preserved.
    """

    out = [list(row) for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0
    seen: set[tuple[int, int]] = set()

    for start_r in range(height):
        for start_c in range(width):
            if out[start_r][start_c] != 1 or (start_r, start_c) in seen:
                continue

            # A frame's blue border is one four-connected component.
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            component: list[tuple[int, int]] = []

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and out[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in component)
            bottom = max(r for r, _ in component)
            left = min(c for _, c in component)
            right = max(c for _, c in component)

            # Ignore degenerate/non-frame components rather than changing cells
            # based only on a bounding box.
            if bottom - top < 2 or right - left < 2:
                continue
            if not all(out[top][c] == 1 and out[bottom][c] == 1 for c in range(left, right + 1)):
                continue
            if not all(out[r][left] == 1 and out[r][right] == 1 for r in range(top, bottom + 1)):
                continue

            contains_red = any(
                out[r][c] == 2
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
            )
            if contains_red:
                for r in range(top + 1, bottom):
                    for c in range(left + 1, right):
                        if out[r][c] == 0:
                            out[r][c] = 3

    return out
