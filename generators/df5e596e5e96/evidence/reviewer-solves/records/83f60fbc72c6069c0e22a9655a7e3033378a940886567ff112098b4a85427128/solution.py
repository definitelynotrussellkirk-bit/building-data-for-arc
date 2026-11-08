from __future__ import annotations


def _normalize(points: set[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    """Translate a finite point set so its top-left occupied cell is at (0, 0)."""
    if not points:
        return frozenset()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return frozenset((row - min_row, col - min_col) for row, col in points)


def _rotate(points: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    """Rotate 90 degrees clockwise around the origin, then remove translation."""
    return _normalize({(col, -row) for row, col in points})


def _reflect(points: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    """Mirror left/right, then remove translation."""
    return _normalize({(row, -col) for row, col in points})


def _relation(
    left: frozenset[tuple[int, int]],
    right: frozenset[tuple[int, int]],
) -> int:
    """Classify two silhouettes: same, rotated, reflected, or unrelated."""
    if left == right:
        return 1

    rotated = right
    for _ in range(3):
        rotated = _rotate(rotated)
        if left == rotated:
            return 2

    reflected = _reflect(right)
    for _ in range(4):
        if left == reflected:
            return 3
        reflected = _rotate(reflected)

    return 0


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Build the pairwise geometric-relation matrix for the five silhouettes."""
    height = len(grid)
    width = len(grid[0])
    stride = height + 1
    count = (width + 1) // stride

    shapes: list[frozenset[tuple[int, int]]] = []
    for index in range(count):
        start = index * stride
        points = {
            (row, col)
            for row in range(height)
            for col in range(height)
            if grid[row][start + col] != 0
        }
        shapes.append(_normalize(points))

    result = [[0] * count for _ in range(count)]
    for row in range(count):
        result[row][row] = 8
        for col in range(row + 1, count):
            relation = _relation(shapes[row], shapes[col])
            result[row][col] = relation
            result[col][row] = relation
    return result
