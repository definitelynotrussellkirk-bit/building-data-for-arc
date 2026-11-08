from collections import deque


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 9) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def solve(grid):
    """Move each component east on walls plus its unchanged source footprint."""
    h, w = len(grid), len(grid[0])
    walls = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    }
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in walls:
        out[r][c] = 9

    for color, cells in _components(grid):
        original = set(cells)
        static_occupied = walls | original
        current = list(cells)
        while True:
            current_set = set(current)
            shifted = [(r, c + 1) for r, c in current]
            if any(
                c >= w
                or ((r, c) in static_occupied and (r, c) not in current_set)
                for r, c in shifted
            ):
                break
            current = shifted
        for r, c in current:
            out[r][c] = color
    return out
