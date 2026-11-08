"""Visible-example solution for blind ARC task e5887c52e323."""

from collections import deque


def solve(grid):
    """Recolor the elbow of each isolated three-cell 2-colored L to 4."""
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue

            component = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                component.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            # A three-cell L occupies a 2x2 box and has a unique cell
            # orthogonally adjacent to both other cells: its elbow.
            if len(component) != 3:
                continue
            rows = {rr for rr, _ in component}
            cols = {cc for _, cc in component}
            if len(rows) != 2 or len(cols) != 2:
                continue

            cells = set(component)
            for rr, cc in component:
                degree = sum(
                    (rr + dr, cc + dc) in cells
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                )
                if degree == 2:
                    out[rr][cc] = 4
                    break

    return out
