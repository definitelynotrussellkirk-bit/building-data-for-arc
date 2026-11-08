from collections import deque


def _components(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    parts = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            part = []
            while q:
                x, y = q.popleft()
                part.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and grid[nx][ny] == color
                        and (nx, ny) not in seen
                    ):
                        seen.add((nx, ny))
                        q.append((nx, ny))
            parts.append(part)
    return parts


def solve(grid):
    """Return the non-singleton object whose color is marked by a singleton."""
    colors = sorted({value for row in grid for value in row if value != 0})

    candidates = []
    for color in colors:
        parts = _components(grid, color)
        has_singleton = any(len(part) == 1 for part in parts)
        non_singletons = [part for part in parts if len(part) > 1]
        if has_singleton and non_singletons:
            object_part = max(non_singletons, key=len)
            candidates.append((len(object_part), color, object_part))

    if not candidates:
        raise ValueError("No color has both a singleton marker and a larger object")

    _, color, object_part = max(candidates)
    r0 = min(r for r, _ in object_part)
    r1 = max(r for r, _ in object_part)
    c0 = min(c for _, c in object_part)
    c1 = max(c for _, c in object_part)
    cells = set(object_part)
    return [
        [color if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]
