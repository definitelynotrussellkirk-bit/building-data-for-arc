from collections import Counter, deque


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append(cells)
    return out


def _shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def solve(grid):
    """Keep the first object's exact oriented shape that occurs only once."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    comps = _components(grid)
    counts = Counter(_shape(cells) for cells in comps)
    unique = [cells for cells in comps if counts[_shape(cells)] == 1]
    if not unique:
        return [[0 for _ in range(w)] for _ in range(h)]
    chosen = min(unique, key=lambda cells: min(cells))
    result = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in chosen:
        result[r][c] = 8
    return result
