"""Visible-example solution for the blind ARC episode.

The input contains three square panels separated by two solid columns.  The
first two panels demonstrate a symmetry; apply that same symmetry to the third.
"""


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _symmetries(grid):
    """Yield the eight dihedral transforms, deduplicated for symmetric grids."""
    seen = set()
    for seed in (grid, _flip_lr(grid)):
        current = [list(row) for row in seed]
        for _ in range(4):
            key = tuple(tuple(row) for row in current)
            if key not in seen:
                seen.add(key)
                yield current
            current = _rotate_cw(current)


def _split_panels(grid):
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    size = len(grid)
    if width != 3 * size + 2:
        raise ValueError("expected three square panels and two separator columns")

    first_sep = size
    second_sep = 2 * size + 1
    for column in (first_sep, second_sep):
        values = {row[column] for row in grid}
        if len(values) != 1 or next(iter(values)) == 0:
            raise ValueError("expected a solid non-background separator column")

    left = [row[:size] for row in grid]
    middle = [row[first_sep + 1 : second_sep] for row in grid]
    right = [row[second_sep + 1 :] for row in grid]
    return left, middle, right


def solve(grid):
    left, middle, right = _split_panels(grid)

    possible_outputs = []
    left_variants = list(_symmetries(left))
    right_variants = list(_symmetries(right))
    # _symmetries emits transforms in the same deterministic order for any grid.
    for transformed_left, transformed_right in zip(left_variants, right_variants):
        if transformed_left == middle:
            possible_outputs.append(transformed_right)

    if not possible_outputs:
        raise ValueError("the first panel has no dihedral symmetry matching the second")

    distinct = {
        tuple(tuple(row) for row in candidate) for candidate in possible_outputs
    }
    if len(distinct) != 1:
        raise ValueError("demonstrated symmetry is ambiguous on the third panel")

    return [list(row) for row in next(iter(distinct))]
