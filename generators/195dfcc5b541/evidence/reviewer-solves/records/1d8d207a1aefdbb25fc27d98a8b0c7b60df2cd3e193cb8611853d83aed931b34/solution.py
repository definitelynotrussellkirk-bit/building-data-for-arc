"""Visible-example solution for the reviewer blind task."""


def _normalize(points):
    """Translate a non-empty collection of (row, col) points to the origin."""
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return frozenset((row - min_row, col - min_col) for row, col in points)


def _dihedral_variants(points):
    """Return all rotations/reflections of a normalized finite cell pattern."""
    variants = set()
    for reflected in (False, True):
        for turns in range(4):
            transformed = []
            for row, col in points:
                x, y = row, -col if reflected else col
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            variants.add(_normalize(transformed))
    return variants


def solve(grid):
    """Recolor every color-3 copy of the color-8 template to color 8.

    Copies may be translated, rotated, or reflected.  Matching is performed
    against the original grid, and the color-3 occupancy of the candidate's
    bounding box must equal the template exactly.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    template_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    }
    if not template_cells:
        return result

    template = _normalize(template_cells)
    recolor = set()

    for variant in _dihedral_variants(template):
        box_height = max(row for row, _ in variant) + 1
        box_width = max(col for _, col in variant) + 1
        for top in range(height - box_height + 1):
            for left in range(width - box_width + 1):
                expected = {
                    (top + row, left + col) for row, col in variant
                }
                actual_threes = {
                    (row, col)
                    for row in range(top, top + box_height)
                    for col in range(left, left + box_width)
                    if grid[row][col] == 3
                }
                if actual_threes == expected:
                    recolor.update(expected)

    for row, col in recolor:
        result[row][col] = 8
    return result
