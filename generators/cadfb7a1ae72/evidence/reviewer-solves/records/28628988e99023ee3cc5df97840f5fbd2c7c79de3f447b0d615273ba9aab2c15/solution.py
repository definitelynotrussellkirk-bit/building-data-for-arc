"""Visible-example solution for the blind ARC episode.

The input contains one monochrome object per non-zero color.  The output is a
pairwise relation matrix over those objects in reading order.
"""


def _objects(grid):
    colors = sorted({cell for row in grid for cell in row if cell != 0})
    objects = []
    for color in colors:
        cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, cell in enumerate(row)
            if cell == color
        }
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        bottom = max(r for r, _ in cells)
        right = max(c for _, c in cells)
        normalized = frozenset((r - top, c - left) for r, c in cells)
        objects.append(((top, left, bottom, right), normalized))
    objects.sort(key=lambda item: (item[0][0], item[0][1]))
    return [shape for _, shape in objects]


def _dimensions(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _mirror_symmetric(shape):
    height, width = _dimensions(shape)
    horizontal = frozenset((height - 1 - r, c) for r, c in shape) == shape
    vertical = frozenset((r, width - 1 - c) for r, c in shape) == shape
    return horizontal and vertical


def _hole_count(shape):
    """Count background components enclosed inside the shape's bounding box."""
    height, width = _dimensions(shape)
    background = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in shape
    }
    holes = 0
    while background:
        seed = next(iter(background))
        stack = [seed]
        component = set()
        touches_boundary = False
        while stack:
            cell = stack.pop()
            if cell not in background:
                continue
            background.remove(cell)
            component.add(cell)
            r, c = cell
            if r in (0, height - 1) or c in (0, width - 1):
                touches_boundary = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in background:
                    stack.append(neighbor)
        if not touches_boundary:
            holes += 1
    return holes


def _normalize(shape):
    top = min(r for r, _ in shape)
    left = min(c for _, c in shape)
    return frozenset((r - top, c - left) for r, c in shape)


def _transforms(shape):
    """Return the distinct rotations/reflections of a normalized shape."""
    result = []
    for reflected in (False, True):
        for turns in range(4):
            transformed = []
            for r, c in shape:
                x, y = r, -c if reflected else c
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            candidate = _normalize(transformed)
            if candidate not in result:
                result.append(candidate)
    return result


def _edit_distance(shape_a, shape_b):
    """Minimum cell symmetric difference under D4 transforms and translation."""
    best = len(shape_a) + len(shape_b)
    for transformed in _transforms(shape_b):
        for ar, ac in shape_a:
            for br, bc in transformed:
                dr, dc = ar - br, ac - bc
                shifted = frozenset((r + dr, c + dc) for r, c in transformed)
                best = min(best, len(shape_a.symmetric_difference(shifted)))
    return best


def solve(grid):
    shapes = _objects(grid)
    size = len(shapes)
    output = [[0 for _ in range(size)] for _ in range(size)]

    for i in range(size):
        output[i][i] = 1
        for j in range(i + 1, size):
            a, b = shapes[i], shapes[j]
            if _mirror_symmetric(a) and _mirror_symmetric(b):
                relation = 8
            elif _hole_count(a) == _hole_count(b) and _edit_distance(a, b) <= 3:
                relation = 4
            else:
                relation = 0
            output[i][j] = relation
            output[j][i] = relation

    return output
