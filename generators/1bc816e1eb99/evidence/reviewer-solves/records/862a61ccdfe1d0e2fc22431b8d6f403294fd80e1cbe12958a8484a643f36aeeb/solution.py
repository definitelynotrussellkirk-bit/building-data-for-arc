from collections import deque


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = [(r, c)]
            seen.add((r, c))
            comp = []
            while todo:
                rr, cc = todo.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            yield comp


def _encloses_hole(component):
    cells = set(component)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)

    # Flood empty cells reachable from the component bounding-box boundary.
    outside = set()
    queue = deque()
    for r in range(r0, r1 + 1):
        for c in (c0, c1):
            if (r, c) not in cells and (r, c) not in outside:
                outside.add((r, c))
                queue.append((r, c))
    for c in range(c0, c1 + 1):
        for r in (r0, r1):
            if (r, c) not in cells and (r, c) not in outside:
                outside.add((r, c))
                queue.append((r, c))

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (r0 <= nr <= r1 and c0 <= nc <= c1 and
                    (nr, nc) not in cells and (nr, nc) not in outside):
                outside.add((nr, nc))
                queue.append((nr, nc))

    return any(
        (r, c) not in cells and (r, c) not in outside
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
    )


def solve(grid):
    out = [row[:] for row in grid]
    for component in _components(grid):
        replacement = 8 if _encloses_hole(component) else 2
        for r, c in component:
            out[r][c] = replacement
    return out
