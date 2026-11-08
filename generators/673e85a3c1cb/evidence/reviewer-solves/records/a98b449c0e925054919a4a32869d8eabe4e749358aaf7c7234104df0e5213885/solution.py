"""Visible-only solution for task 673e85a3c1cb."""


def _rotate_cw(grid):
    """Return a 90-degree clockwise rotation of a rectangular grid."""
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    """Mirror a grid left-to-right."""
    return [list(reversed(row)) for row in grid]


def _dihedral_images(grid):
    """Yield the eight square-grid symmetries as (recipe, image) pairs."""
    current = [list(row) for row in grid]
    for turns in range(4):
        yield (turns, False), current
        yield (turns, True), _flip_lr(current)
        current = _rotate_cw(current)


def _apply_recipe(grid, recipe):
    turns, mirror = recipe
    result = [list(row) for row in grid]
    for _ in range(turns):
        result = _rotate_cw(result)
    if mirror:
        result = _flip_lr(result)
    return result


def solve(grid):
    """Infer the demonstrated symmetry and apply it to the lower-left tile.

    A complete row and column of 9s split the input into four equal tiles.  The
    upper-right tile is one of the eight rotations/reflections of the upper-left
    tile.  The same transformation is applied to the lower-left tile; the
    lower-right tile is a blank answer area and is not part of the returned grid.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    divider_cols = [
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    ]
    if len(divider_rows) != 1 or len(divider_cols) != 1:
        raise ValueError("expected one all-9 divider row and one all-9 divider column")

    split_row = divider_rows[0]
    split_col = divider_cols[0]
    top_left = [row[:split_col] for row in grid[:split_row]]
    top_right = [row[split_col + 1 :] for row in grid[:split_row]]
    bottom_left = [row[:split_col] for row in grid[split_row + 1 :]]

    if not top_left or len(top_left) != len(top_left[0]):
        raise ValueError("expected non-empty square tiles")
    if [len(top_left), len(top_left[0])] != [len(top_right), len(top_right[0])]:
        raise ValueError("upper tiles must have equal shapes")
    if [len(top_left), len(top_left[0])] != [len(bottom_left), len(bottom_left[0])]:
        raise ValueError("source tiles must have equal shapes")

    matches = [recipe for recipe, image in _dihedral_images(top_left) if image == top_right]
    if not matches:
        raise ValueError("upper-right tile is not a rotation/reflection of upper-left")

    # The authored examples make the demonstrated action identifiable.  Taking
    # the first recipe also behaves deterministically for an accidentally
    # symmetric demonstration.
    return _apply_recipe(bottom_left, matches[0])
