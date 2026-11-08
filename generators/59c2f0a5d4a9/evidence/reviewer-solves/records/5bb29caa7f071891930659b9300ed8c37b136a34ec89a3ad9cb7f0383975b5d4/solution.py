"""Visible-example solution for task 59c2f0a5d4a9."""

from collections import deque


def solve(grid):
    """Fill a 1-bordered rectangle's interior with 4 when it contains a 2."""
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()

    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 1 or (r0, c0) in seen:
                continue

            # Each rectangular frame is a 4-connected component of color 1.
            q = deque([(r0, c0)])
            seen.add((r0, c0))
            component = []
            while q:
                r, c = q.popleft()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))

            top = min(r for r, _ in component)
            bottom = max(r for r, _ in component)
            left = min(c for _, c in component)
            right = max(c for _, c in component)
            if bottom - top < 2 or right - left < 2:
                continue

            perimeter = (
                [(top, c) for c in range(left, right + 1)]
                + [(bottom, c) for c in range(left, right + 1)]
                + [(r, left) for r in range(top + 1, bottom)]
                + [(r, right) for r in range(top + 1, bottom)]
            )
            if not all(grid[r][c] == 1 for r, c in perimeter):
                continue

            has_marker = any(
                grid[r][c] == 2
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
            )
            if has_marker:
                for r in range(top + 1, bottom):
                    for c in range(left + 1, right):
                        out[r][c] = 4

    return out
