def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return grid[::-1]


def _anti_transpose(grid):
    return _rotate_180(_transpose(grid))


def solve(grid):
    """Decode the top-row color-sum and transform the cropped lower pattern."""
    if not grid or not grid[0]:
        return []

    # The detached cells in the first row are an operation key.  Their color
    # values sum to the dihedral-operation code (modulo eight).
    code = sum(value for value in grid[0] if value != 0) % 8

    # Everything below the key belongs to the payload.  Crop its nonzero bbox.
    points = [
        (r, c)
        for r, row in enumerate(grid[1:], start=1)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not points:
        return []

    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    payload = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    transforms = {
        0: lambda x: [row[:] for row in x],
        1: _anti_transpose,
        2: _rotate_180,
        3: _transpose,
        4: _flip_lr,
        5: _rotate_ccw,
        6: _flip_ud,
        7: _rotate_cw,
    }
    return transforms[code](payload)
