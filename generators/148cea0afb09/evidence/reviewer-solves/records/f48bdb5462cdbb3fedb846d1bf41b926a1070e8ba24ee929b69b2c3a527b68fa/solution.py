from collections import deque


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    parts = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            parts.append((color, cells))
    return parts


def solve(grid):
    if not grid or not grid[0]:
        return []

    rank = grid[0][0]
    work = [row[:] for row in grid]
    work[0][0] = 0
    components = _components(work)
    components.sort(key=lambda item: len(item[1]))
    if not isinstance(rank, int) or rank < 1 or rank > len(components):
        raise ValueError("top-left marker must be a valid 1-based object rank")

    color, cells = components[rank - 1]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    crop = [
        [color if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    result = []
    for row in crop:
        doubled = [value for value in row for _ in range(2)]
        result.extend([doubled[:], doubled[:]])
    return result
