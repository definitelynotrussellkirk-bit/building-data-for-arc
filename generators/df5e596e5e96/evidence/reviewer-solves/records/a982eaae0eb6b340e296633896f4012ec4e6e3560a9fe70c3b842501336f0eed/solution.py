"""Visible-example solution for the blind ARC puzzle.

The 5x29 input is five 5x5 silhouettes separated by one blank column.
The output is their pairwise relation matrix:
  8 diagonal, 1 same orientation, 2 rotation, 3 reflection, 0 unrelated.
Colors are ignored; only occupied-cell geometry matters.
"""


def _normalise(points):
    """Translate an iterable of (row, col) points to a canonical origin."""
    points = list(points)
    if not points:
        return ()
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _rotate(points):
    """Rotate points 90 degrees clockwise around the origin."""
    return [(c, -r) for r, c in points]


def _reflect(points):
    """Reflect points across a vertical axis through the origin."""
    return [(r, -c) for r, c in points]


def _relation(a, b):
    """Classify b relative to a, ignoring translation and cell color."""
    target = _normalise(b)
    current = list(a)

    # Translation only: unchanged orientation.
    if _normalise(current) == target:
        return 1

    # Proper rotations (90, 180, or 270 degrees).
    for _ in range(3):
        current = _rotate(current)
        if _normalise(current) == target:
            return 2

    # Any reflected orientation (mirror, possibly followed by rotation).
    current = _reflect(list(a))
    for _ in range(4):
        if _normalise(current) == target:
            return 3
        current = _rotate(current)

    return 0


def solve(grid):
    height = len(grid)
    width = len(grid[0])

    # The examples establish five equal-width panels with four one-column gaps.
    panel_count = 5
    panel_width = (width - (panel_count - 1)) // panel_count
    stride = panel_width + 1

    shapes = []
    for panel in range(panel_count):
        left = panel * stride
        points = []
        for r in range(height):
            for c in range(panel_width):
                if grid[r][left + c] != 0:
                    points.append((r, c))
        shapes.append(points)

    out = [[0] * panel_count for _ in range(panel_count)]
    for i in range(panel_count):
        out[i][i] = 8
        for j in range(i + 1, panel_count):
            value = _relation(shapes[i], shapes[j])
            out[i][j] = value
            out[j][i] = value
    return out
