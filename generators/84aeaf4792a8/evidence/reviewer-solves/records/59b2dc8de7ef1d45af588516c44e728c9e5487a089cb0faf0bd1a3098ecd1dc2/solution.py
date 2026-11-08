"""Shape-rotation equivalence inferred from the three visible demonstrations."""


def _normalise(points):
    top = min(r for r, _ in points)
    left = min(c for _, c in points)
    return tuple(sorted((r - top, c - left) for r, c in points))


def _rotation_key(points):
    keys = []
    current = list(points)
    for _ in range(4):
        keys.append(_normalise(current))
        current = [(c, -r) for r, c in current]
    return min(keys)


def solve(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                y, x = stack.pop()
                component.append((y, x))
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (0 <= yy < height and 0 <= xx < width
                            and (yy, xx) not in seen and grid[yy][xx] == color):
                        seen.add((yy, xx))
                        stack.append((yy, xx))
            objects.append(_rotation_key(component))
    return [[5 if i == j else 8 if a == b else 0
             for j, b in enumerate(objects)] for i, a in enumerate(objects)]
