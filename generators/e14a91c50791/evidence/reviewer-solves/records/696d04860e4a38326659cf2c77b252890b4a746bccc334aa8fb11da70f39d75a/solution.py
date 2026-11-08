from collections import Counter, defaultdict


def _components(grid):
    """Return 4-connected components of non-background cells."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and (nx, ny) not in seen
                        and grid[nx][ny] == color
                    ):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            components.append((color, cells))
    return components


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_key(cells):
    """Canonical polyomino key, treating rotations/reflections as equivalent."""
    variants = []
    current = list(cells)
    for reflected in (False, True):
        transformed = [(r, -c if reflected else c) for r, c in current]
        for _ in range(4):
            variants.append(_normalize(transformed))
            transformed = [(c, -r) for r, c in transformed]
    return min(variants)


def solve(grid):
    components = _components(grid)
    by_shape = defaultdict(list)
    for color, cells in components:
        by_shape[_shape_key(cells)].append((color, cells))

    # The examples contain paired shape classes plus one class occurring an odd
    # number of times.  Every member of that odd class is completed to its
    # bounding rectangle and recolored azure (7).
    odd_shapes = {shape for shape, members in by_shape.items() if len(members) % 2 == 1}
    result = [row[:] for row in grid]
    for shape in odd_shapes:
        for _color, cells in by_shape[shape]:
            r0 = min(r for r, _ in cells)
            r1 = max(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            c1 = max(c for _, c in cells)
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    result[r][c] = 7
    return result
