"""Visible-example solution for task 60c27b9638fb."""


def _crop_payload(grid):
    """Remove the isolated instruction at (0, 0) and crop remaining color cells."""
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
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_clockwise(block):
    return [list(row) for row in zip(*block[::-1])]


def _rotate_180(block):
    return [list(reversed(row)) for row in reversed(block)]


def _reflect_left_right(block):
    return [list(reversed(row)) for row in block]


def solve(grid):
    """Crop the payload and apply the symmetry encoded by the corner color."""
    instruction = grid[0][0]
    block = _crop_payload(grid)

    if instruction == 1:
        return _rotate_clockwise(block)
    if instruction == 2:
        return _rotate_180(block)
    if instruction == 3:
        return _reflect_left_right(block)

    # No unseen instruction is needed by the visible challenge. Keeping the
    # payload unchanged is the least-assumptive fallback.
    return block
