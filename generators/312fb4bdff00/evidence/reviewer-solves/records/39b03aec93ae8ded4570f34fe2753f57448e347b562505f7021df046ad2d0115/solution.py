def _normalize(points):
    """Translate a finite point set to a zero-based bounding box."""
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return frozenset((r - min_r, c - min_c) for r, c in points)


def _shape_key(points):
    """Canonical key up to translation, quarter-turns, and reflection."""
    variants = []
    for reflected in (False, True):
        for turns in range(4):
            transformed = set()
            for r, c in points:
                x, y = r, (-c if reflected else c)
                for _ in range(turns):
                    x, y = y, -x
                transformed.add((x, y))
            variants.append(tuple(sorted(_normalize(transformed))))
    return min(variants)


def solve(grid):
    """Find a transformed twin of the first panel and render its source shape."""
    marker_cells = [(c, value) for c, value in enumerate(grid[0]) if value != 0]
    if not marker_cells:
        return [[0]]
    marker_col, marker_color = marker_cells[0]

    panel_starts = (0, 5, 10, 15)
    shapes = []
    for start in panel_starts:
        points = {
            (r - 1, c - start)
            for r in range(1, min(5, len(grid)))
            for c in range(start, min(start + 4, len(grid[r])))
            if grid[r][c] != 0
        }
        shapes.append(points)

    source = shapes[0]
    if not source:
        return [[0]]
    source_key = _shape_key(source)
    if not any(candidate and _shape_key(candidate) == source_key for candidate in shapes[1:]):
        return [[0]]

    normalized = _normalize(source)
    height = max(r for r, _ in normalized) + 1
    width = max(c for _, c in normalized) + 1

    # The marker's position within its four-cell panel is the horizontal anchor.
    target_col = marker_col % 5
    anchor_col = (width - 1) // 2
    left = max(0, min(4 - width, target_col - anchor_col))
    top = (5 - height) // 2  # ceil((4 - height) / 2): lower-centre even ties.

    output = [[0 for _ in range(4)] for _ in range(4)]
    for r, c in normalized:
        output[top + r][left + c] = marker_color
    return output
