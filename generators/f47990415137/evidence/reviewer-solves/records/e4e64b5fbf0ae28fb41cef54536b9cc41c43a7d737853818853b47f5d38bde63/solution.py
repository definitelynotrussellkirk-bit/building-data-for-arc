"""Visible-example solution for the blind ARC episode."""

from collections import deque


def solve(grid):
    """Recolor each 4-connected nonzero object by bounding-box orientation.

    Taller-than-wide objects become 2, wider-than-tall objects become 3,
    and square-bounding-box objects become 4. Background remains zero.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = [[False] * width for _ in range(height)]

    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] == 0 or seen[r0][c0]:
                continue

            color = grid[r0][c0]
            queue = deque([(r0, c0)])
            seen[r0][c0] = True
            cells = []

            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            box_height = max(rows) - min(rows) + 1
            box_width = max(cols) - min(cols) + 1
            new_color = 2 if box_height > box_width else 3 if box_width > box_height else 4
            for r, c in cells:
                out[r][c] = new_color

    return out
