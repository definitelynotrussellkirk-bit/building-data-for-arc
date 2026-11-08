"""Visible-example inference: compare monochrome shapes under rotation."""


def _normalize(points):
    row0 = min(row for row, col in points)
    col0 = min(col for row, col in points)
    return tuple(sorted((row - row0, col - col0) for row, col in points))


def _rotation_key(points):
    variants = []
    rotated = list(points)
    for _ in range(4):
        variants.append(_normalize(rotated))
        rotated = [(col, -row) for row, col in rotated]
    return min(variants)


def solve(grid):
    by_color = {}
    for row, cells in enumerate(grid):
        for col, color in enumerate(cells):
            if color != 0:
                by_color.setdefault(color, []).append((row, col))

    objects = sorted(
        by_color.values(),
        key=lambda points: min(col for row, col in points),
    )
    keys = [_rotation_key(points) for points in objects]
    return [
        [8 if i == j else (2 if key_i == key_j else 0)
         for j, key_j in enumerate(keys)]
        for i, key_i in enumerate(keys)
    ]

