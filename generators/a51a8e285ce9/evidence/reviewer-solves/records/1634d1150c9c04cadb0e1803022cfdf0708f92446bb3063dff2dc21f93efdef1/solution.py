"""Visible-only solution for the assigned ARC puzzle."""


def _crop(mask):
    rows = [r for r, row in enumerate(mask) if any(row)]
    cols = [c for c in range(len(mask[0])) if any(row[c] for row in mask)]
    if not rows or not cols:
        return []
    return [row[cols[0] : cols[-1] + 1] for row in mask[rows[0] : rows[-1] + 1]]


def _rotate_clockwise(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _shape_key(shape):
    return tuple(tuple(row) for row in shape)


def _dihedral_keys(shape):
    """All rotations/reflections of a cropped binary shape."""
    variants = set()
    current = shape
    for _ in range(4):
        variants.add(_shape_key(current))
        variants.add(_shape_key([row[::-1] for row in current]))
        current = _rotate_clockwise(current)
    return variants


def _binary_panel(grid, start, width):
    return [[1 if value != 0 else 0 for value in row[start : start + width]] for row in grid]


def solve(grid):
    if not grid or not grid[0]:
        return []

    total_width = len(grid[0])
    if (total_width - 2) % 3:
        raise ValueError("expected three equal panels separated by two columns")

    panel_width = (total_width - 2) // 3
    starts = (0, panel_width + 1, 2 * panel_width + 2)
    shapes = [_crop(_binary_panel(grid, start, panel_width)) for start in starts]

    selector_values = {
        value
        for row in grid
        for value in row[starts[2] : starts[2] + panel_width]
        if value != 0
    }
    if len(selector_values) != 1:
        raise ValueError("expected one non-background selector color")
    selector_color = next(iter(selector_values))

    selector_variants = _dihedral_keys(shapes[2])
    for candidate in shapes[:2]:
        if _shape_key(candidate) in selector_variants:
            return [
                [selector_color if cell else 0 for cell in row]
                for row in candidate
            ]

    raise ValueError("neither source shape matches the selector up to symmetry")
