"""Solve the visible three-frame transformation analogy."""


def _components_of_ones(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and grid[nx][ny] == 1
                        and (nx, ny) not in seen
                    ):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            components.append(comp)
    return components


def _frame_boxes(grid):
    boxes = set()
    for comp in _components_of_ones(grid):
        rows = [p[0] for p in comp]
        cols = [p[1] for p in comp]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        perimeter = (
            [(r0, c) for c in range(c0, c1 + 1)]
            + [(r1, c) for c in range(c0, c1 + 1)]
            + [(r, c0) for r in range(r0 + 1, r1)]
            + [(r, c1) for r in range(r0 + 1, r1)]
        )
        if all(grid[r][c] == 1 for r, c in perimeter):
            boxes.add((r0, c0, r1, c1))
    return sorted(boxes, key=lambda b: (b[0], b[1]))


def _tight_crop(matrix):
    occupied = [
        (r, c)
        for r, row in enumerate(matrix)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return [[0]]
    r0 = min(r for r, _ in occupied)
    r1 = max(r for r, _ in occupied)
    c0 = min(c for _, c in occupied)
    c1 = max(c for _, c in occupied)
    return [row[c0 : c1 + 1] for row in matrix[r0 : r1 + 1]]


def _rotate_clockwise(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def _apply_transform(matrix, transform_name):
    current = [row[:] for row in matrix]
    rotations = int(transform_name[1])
    for _ in range(rotations):
        current = _rotate_clockwise(current)
    if transform_name.endswith("f"):
        current = [row[::-1] for row in current]
    return current


def _named_transforms(matrix):
    names = ("r0", "r0f", "r1", "r1f", "r2", "r2f", "r3", "r3f")
    return [(name, _apply_transform(matrix, name)) for name in names]


def solve(grid):
    boxes = _frame_boxes(grid)
    if len(boxes) < 3:
        raise ValueError(f"expected three rectangular frames, found {len(boxes)}")

    pieces = []
    for r0, c0, r1, c1 in boxes[:3]:
        interior = [row[c0 + 1 : c1] for row in grid[r0 + 1 : r1]]
        pieces.append(_tight_crop(interior))

    source, transformed_source, query = pieces
    matches = [
        name
        for name, candidate in _named_transforms(source)
        if candidate == transformed_source
    ]
    if not matches:
        raise ValueError("the first two framed patterns do not define a dihedral transform")

    # Generated lessons are expected to make this transform identifiable. If the
    # source itself is symmetric, use a stable canonical representative.
    return _apply_transform(query, matches[0])
