from collections import deque


def _solid_3x3_objects(grid):
    """Return (center_row, center_col, color) for exact 3x3 color components."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    objects = []

    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or seen[r0][c0]:
                continue

            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))

            if len(cells) != 9:
                continue
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            if r2 - r1 == 2 and c2 - c1 == 2:
                expected = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
                if set(cells) == expected:
                    objects.append((r1 + 1, c1 + 1, color))

    return objects


def solve(grid):
    out = [row[:] for row in grid]
    objects = _solid_3x3_objects(grid)

    horizontal = {}
    vertical = {}
    for r, c, color in objects:
        horizontal.setdefault(r, set()).add(color)
        vertical.setdefault(c, set()).add(color)

    for r in range(len(grid)):
        for c in range(len(grid[0])):
            colors = set()
            colors.update(horizontal.get(r, ()))
            colors.update(vertical.get(c, ()))
            if colors:
                out[r][c] = next(iter(colors)) if len(colors) == 1 else 0

    return out
