from collections import deque


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            yield color, cells


def solve(grid):
    """Fill the unique geometric center of each odd-by-odd hollow rectangle."""
    out = [row[:] for row in grid]
    for color, cells in _components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        height = r1 - r0 + 1
        width = c1 - c0 + 1

        if height < 3 or width < 3 or height % 2 == 0 or width % 2 == 0:
            continue

        expected_border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if set(cells) != expected_border:
            continue

        center = ((r0 + r1) // 2, (c0 + c1) // 2)
        if out[center[0]][center[1]] == 0:
            out[center[0]][center[1]] = color
    return out
