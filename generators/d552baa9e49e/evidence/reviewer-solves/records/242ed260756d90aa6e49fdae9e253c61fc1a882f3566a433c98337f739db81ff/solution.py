"""Visible-only solution for blind task d552baa9e49e."""


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _rotate_clockwise(grid):
    return _transpose(grid[::-1])


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _mirror_horizontal(grid):
    return [row[::-1] for row in grid]


def solve(grid):
    """Crop the non-background payload and apply the marker-coded symmetry.

    The isolated nonzero cell at the upper-left is the operation marker.  The
    remaining nonzero cells define a tight rectangular payload; interior zeros
    are retained.  Visible examples establish marker 1 = clockwise quarter-turn,
    marker 2 = half-turn, and marker 3 = main-diagonal transpose.  Marker 4 is
    inferred as the remaining paired operation, a left/right mirror.
    """
    if not grid or not grid[0]:
        return []

    marker = grid[0][0]
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    if not points:
        return []

    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    payload = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    transforms = {
        1: _rotate_clockwise,
        2: _rotate_180,
        3: _transpose,
        4: _mirror_horizontal,
    }
    transform = transforms.get(marker)
    if transform is None:
        raise ValueError(f"unsupported operation marker: {marker!r}")
    return transform(payload)
