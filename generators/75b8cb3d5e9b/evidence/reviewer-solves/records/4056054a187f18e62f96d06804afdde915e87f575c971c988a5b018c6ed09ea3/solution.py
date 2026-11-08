"""Visible-only solver for the three-panel transformation analogy task."""


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _dihedral_transforms(grid):
    """Return the eight square-grid symmetries in a stable order."""
    r0 = [row[:] for row in grid]
    r1 = _rotate_cw(r0)
    r2 = _rotate_cw(r1)
    r3 = _rotate_cw(r2)
    f0 = [row[::-1] for row in r0]
    f1 = _rotate_cw(f0)
    f2 = _rotate_cw(f1)
    f3 = _rotate_cw(f2)
    return [r0, r1, r2, r3, f0, f1, f2, f3]


def _split_panels(grid):
    """Split on solid non-background separator columns."""
    height = len(grid)
    width = len(grid[0])
    separators = [
        c
        for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    ]
    if len(separators) != 2:
        raise ValueError(f"expected two separator columns, found {separators}")

    bounds = [(0, separators[0]), (separators[0] + 1, separators[1]), (separators[1] + 1, width)]
    return [[row[left:right] for row in grid] for left, right in bounds]


def _remove_padding_column(panel):
    """Remove the single blank edge column from a 3-by-4 panel."""
    if len(panel[0]) < 2:
        raise ValueError("panel is too narrow")

    left_blank = all(row[0] == 0 for row in panel)
    right_blank = all(row[-1] == 0 for row in panel)

    if left_blank and not right_blank:
        return [row[1:] for row in panel]
    if right_blank and not left_blank:
        return [row[:-1] for row in panel]
    if left_blank and right_blank:
        # Either crop is possible for a doubly padded panel.  The generated
        # lessons normally avoid this; retain a deterministic fallback.
        return [row[1:] for row in panel]
    raise ValueError("panel has no blank edge padding column")


def solve(grid):
    first, second, query = (_remove_padding_column(p) for p in _split_panels(grid))

    matches = [i for i, transformed in enumerate(_dihedral_transforms(first)) if transformed == second]
    if not matches:
        raise ValueError("no rotation/reflection maps the first panel to the second")

    candidates = [_dihedral_transforms(query)[i] for i in matches]
    if any(candidate != candidates[0] for candidate in candidates[1:]):
        raise ValueError("visible analogy is ambiguous on the query panel")
    return candidates[0]
