"""Visible-example solution for the three-panel crop-transform task."""


def _crop_nonzero(grid):
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not points:
        return []
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _identity(grid):
    return [row[:] for row in grid]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return [row[:] for row in grid[::-1]]


_TRANSFORMS = (
    _identity,
    _rotate_cw,
    _rotate_180,
    _rotate_ccw,
    _flip_lr,
    _flip_ud,
)


def _split_panels(grid):
    width = len(grid[0])
    separators = [
        c for c in range(width) if all(row[c] == 9 for row in grid)
    ]
    if len(separators) != 2:
        raise ValueError("expected exactly two full-height color-9 separators")
    left, right = separators
    ranges = ((0, left), (left + 1, right), (right + 1, width))
    return [[row[start:stop] for row in grid] for start, stop in ranges]


def solve(grid):
    panel_a, panel_b, panel_c = _split_panels(grid)
    a = _crop_nonzero(panel_a)
    b = _crop_nonzero(panel_b)
    c = _crop_nonzero(panel_c)
    for transform in _TRANSFORMS:
        if transform(a) == b:
            return transform(c)
    raise ValueError("no demonstrated transform maps the first crop to the second")
