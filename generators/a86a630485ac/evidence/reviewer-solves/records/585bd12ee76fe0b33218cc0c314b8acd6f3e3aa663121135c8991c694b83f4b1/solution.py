"""Visible-example solver for the post-repair ARC episode."""

from collections import deque


def solve(grid):
    """Keep exactly the left-right symmetric nonzero connected components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]
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

            min_c = min(c for _, c in component)
            max_c = max(c for _, c in component)
            occupied = set(component)
            lr_symmetric = all((r, min_c + max_c - c) in occupied for r, c in component)
            if lr_symmetric:
                for r, c in component:
                    out[r][c] = color

    return out
