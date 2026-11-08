from collections import deque


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and grid[nx][ny] == color and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        q.append((nx, ny))
            yield cells


def solve(grid):
    """Select the outlined box with the most 2s; fill its empty interior with 3."""
    candidates = []
    for cells in _components(grid, 1):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if set(cells) != border:
            continue
        dots = sum(
            grid[r][c] == 2
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        )
        candidates.append((-dots, r0, c0, r1, c1))

    if not candidates:
        return [row[:] for row in grid]

    _, r0, c0, r1, c1 = min(candidates)
    out = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    for r in range(1, len(out) - 1):
        for c in range(1, len(out[0]) - 1):
            if out[r][c] == 0:
                out[r][c] = 3
    return out
