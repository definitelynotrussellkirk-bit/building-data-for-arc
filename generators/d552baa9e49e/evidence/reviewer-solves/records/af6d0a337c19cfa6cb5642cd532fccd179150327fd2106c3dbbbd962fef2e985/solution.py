def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid):
    """Crop the payload and apply the transform encoded by the corner marker."""
    marker = grid[0][0]
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    if not cells:
        return []

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    payload = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    if marker == 1:
        return _rotate_clockwise(payload)
    if marker == 2:
        return _rotate_clockwise(_rotate_clockwise(payload))
    if marker == 3:
        return [list(row) for row in zip(*payload)]
    if marker == 4:
        # Marker 4 is absent from the visible training examples. Identity is the
        # minimum-complexity extrapolation after the three observed transforms.
        return payload
    return payload
