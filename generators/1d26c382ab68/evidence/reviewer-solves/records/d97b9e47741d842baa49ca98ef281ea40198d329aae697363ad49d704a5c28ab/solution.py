from collections import deque


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _rotations(cells):
    """Return all translation-normalized quarter-turn rotations."""
    shape = _normalize(cells)
    variants = set()
    for _ in range(4):
        shape = _normalize(shape)
        variants.add(shape)
        shape = frozenset((c, -r) for r, c in shape)
    return variants


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def solve(grid):
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    separator = next(
        r for r, row in enumerate(grid)
        if row and all(value == 9 for value in row)
    )

    template = {
        (r, c)
        for r in range(separator)
        for c in range(width)
        if grid[r][c] not in (0, 9)
    }
    rotated_templates = _rotations(template)

    lower_cells = {
        (r, c)
        for r in range(separator + 1, height)
        for c in range(width)
        if grid[r][c] not in (0, 9)
    }

    for component in _components(lower_cells):
        if _normalize(component) in rotated_templates:
            for r, c in component:
                out[r][c] = 2
            break

    return out
