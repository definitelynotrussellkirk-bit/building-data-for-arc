"""Visible-example solution for the generated ARC episode.

The color-8 cells form a small stencil.  Every color-3 occurrence of that
stencil, under any rotation or reflection, is recolored to 8.  Other cells are
left unchanged.
"""


def _normalize(points):
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _dihedral_variants(points):
    variants = set()
    for reflected in (False, True):
        for turns in range(4):
            transformed = []
            for row, col in points:
                r, c = row, (-col if reflected else col)
                for _ in range(turns):
                    r, c = c, -r
                transformed.append((r, c))
            variants.add(_normalize(transformed))
    return sorted(variants)


def solve(grid):
    """Return a copy with every transformed color-3 stencil changed to 8."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    stencil = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if not stencil:
        return [list(row) for row in grid]

    stencil = _normalize(stencil)
    matched_cells = set()

    for variant in _dihedral_variants(stencil):
        variant_h = max(row for row, _ in variant) + 1
        variant_w = max(col for _, col in variant) + 1
        for top in range(height - variant_h + 1):
            for left in range(width - variant_w + 1):
                placed = {(top + row, left + col) for row, col in variant}
                if all(grid[row][col] == 3 for row, col in placed):
                    matched_cells.update(placed)

    result = [list(row) for row in grid]
    for row, col in matched_cells:
        result[row][col] = 8
    return result
