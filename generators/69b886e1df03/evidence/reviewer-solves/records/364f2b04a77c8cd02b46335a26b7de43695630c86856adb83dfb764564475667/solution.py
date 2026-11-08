"""Visible-example solution for the blind ARC episode."""

from collections import deque


def solve(grid):
    """Complete every non-linear 4-connected colored object to its bounding box.

    Background is color 0.  A component that occupies only one row or one column
    is a line and is left unchanged.  Components spanning both axes are replaced
    by their solid axis-aligned bounding rectangle in the component's color.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue

            component = []
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            r_min, r_max = min(rows), max(rows)
            c_min, c_max = min(cols), max(cols)

            if r_min < r_max and c_min < c_max:
                for r in range(r_min, r_max + 1):
                    for c in range(c_min, c_max + 1):
                        out[r][c] = color

    return out
