"""Visible-only solution for the reviewer blind episode."""


def _normalize(points):
    if not points:
        return ()
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _shape_signature(points):
    """Canonicalize a finite cell set up to translation and D4 symmetry."""
    transforms = []
    for kind in range(8):
        moved = []
        for r, c in points:
            if kind == 0:
                rr, cc = r, c
            elif kind == 1:
                rr, cc = r, -c
            elif kind == 2:
                rr, cc = -r, c
            elif kind == 3:
                rr, cc = -r, -c
            elif kind == 4:
                rr, cc = c, r
            elif kind == 5:
                rr, cc = c, -r
            elif kind == 6:
                rr, cc = -c, r
            else:
                rr, cc = -c, -r
            moved.append((rr, cc))
        transforms.append(_normalize(moved))
    return min(transforms)


def _panels(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0

    # The visible examples use full-height 9-columns as panel separators.
    separators = {
        c
        for c in range(width)
        if height and all(grid[r][c] == 9 for r in range(height))
    }

    spans = []
    start = 0
    for c in range(width + 1):
        if c == width or c in separators:
            if start < c:
                spans.append((start, c))
            start = c + 1

    result = []
    for left, right in spans:
        points = {
            (r, c - left)
            for r in range(height)
            for c in range(left, right)
            if grid[r][c] != 0
        }
        result.append(points)
    return result


def solve(grid):
    shapes = [_shape_signature(points) for points in _panels(grid)]
    size = len(shapes)
    return [
        [8 if shapes[row] == shapes[col] else 0 for col in range(size)]
        for row in range(size)
    ]
