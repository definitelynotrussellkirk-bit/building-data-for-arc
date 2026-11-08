"""Visible-only solution for the blind ARC episode.

Keep each non-background 4-connected object whose occupied cells are symmetric
under reflection across the vertical axis of that object's bounding box.
"""


def solve(grid):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [[0 for _ in range(cols)] for _ in range(rows)]
    seen = set()

    for r0 in range(rows):
        for c0 in range(cols):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue

            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            min_c = min(c for _, c in cells)
            max_c = max(c for _, c in cells)
            occupied = set(cells)
            vertically_symmetric = all(
                (r, min_c + max_c - c) in occupied for r, c in cells
            )
            if vertically_symmetric:
                for r, c in cells:
                    out[r][c] = color

    return out
