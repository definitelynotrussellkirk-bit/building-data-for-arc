"""Visible-example solution for the assigned ARC task.

The input contains three equally sized square panels separated by one-column
bars.  The first two panels define one of the eight symmetries of a square;
the output is that same symmetry applied to the third panel.
"""


def _rotate_90(grid):
    """Rotate a square grid 90 degrees clockwise."""
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rotate_270(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _flip_top_bottom(grid):
    return [row[:] for row in grid[::-1]]


def _flip_left_right(grid):
    return [row[::-1] for row in grid]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _reflect_anti_diagonal(grid):
    # Transpose, then rotate 180 degrees.
    return _rotate_180(_transpose(grid))


def _identity(grid):
    return [row[:] for row in grid]


_TRANSFORMS = (
    _identity,
    _rotate_90,
    _rotate_180,
    _rotate_270,
    _flip_top_bottom,
    _flip_left_right,
    _transpose,
    _reflect_anti_diagonal,
)


def _split_panels(grid):
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    size = len(grid)
    expected_width = 3 * size + 2
    if len(grid[0]) != expected_width:
        raise ValueError(
            f"expected three {size}x{size} panels and two separators; "
            f"got width {len(grid[0])}"
        )

    # The visible examples use full 9-valued separator columns.  Validate the
    # framing so an accidental malformed split cannot silently look plausible.
    separator_columns = (size, 2 * size + 1)
    if any(any(row[column] != 9 for row in grid) for column in separator_columns):
        raise ValueError("expected full color-9 separator columns")

    starts = (0, size + 1, 2 * size + 2)
    return [
        [row[start : start + size] for row in grid]
        for start in starts
    ]


def solve(grid):
    first, second, payload = _split_panels(grid)

    matches = [transform for transform in _TRANSFORMS if transform(first) == second]
    if not matches:
        raise ValueError("the first two panels do not define a square symmetry")

    # A well-formed puzzle supplies a unique observable mapping.  In a symmetric
    # edge case, accept multiple descriptions only when they agree on the payload.
    outputs = [transform(payload) for transform in matches]
    if any(output != outputs[0] for output in outputs[1:]):
        raise ValueError("the demonstrated symmetry is ambiguous on the payload")
    return outputs[0]
