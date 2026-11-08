from collections import deque


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append((color, tuple(sorted(cells))))
    return found


def normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def rotate(shape):
    shape = normalize(shape)
    height = max(r for r, _ in shape) + 1
    return normalize((c, height - 1 - r) for r, c in shape)


def rotations(shape):
    result = set()
    current = normalize(shape)
    for _ in range(4):
        result.add(current)
        current = rotate(current)
    return result


def bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def solve(grid):
    h, w = len(grid), len(grid[0])
    target = grid[0][w - 1]
    marker = (0, w - 1)
    objs = [(color, cells) for color, cells in components(grid)
            if not (len(cells) == 1 and cells[0] == marker)]
    refs = [(color, cells) for color, cells in objs if color == 1]
    ref = sorted(refs, key=lambda item: (-len(item[1]), bbox(item[1])[:2]))[0]
    candidates = sorted([item for item in objs if item != ref],
                        key=lambda item: bbox(item[1])[:2])
    allowed = rotations(ref[1])
    match = next(cells for _, cells in candidates if normalize(cells) in allowed)
    r0, c0, r1, c1 = bbox(match)
    occupied = set(match)
    return [[target if (r, c) in occupied else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]
