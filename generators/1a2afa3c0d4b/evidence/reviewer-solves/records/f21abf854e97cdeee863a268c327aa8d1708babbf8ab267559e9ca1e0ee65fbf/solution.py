def _rotate_ccw(square):
    n = len(square)
    return [[square[c][n - 1 - r] for c in range(n)] for r in range(n)]


def _flip_left_right(square):
    return [list(reversed(row)) for row in square]


def _dihedral_transforms(square):
    """Return the eight square symmetries as (name, transformed grid)."""
    result = []
    for reflected, start in (
        (False, [row[:] for row in square]),
        (True, _flip_left_right(square)),
    ):
        current = start
        for quarter_turns in range(4):
            result.append(
                (
                    (reflected, quarter_turns),
                    [row[:] for row in current],
                )
            )
            current = _rotate_ccw(current)
    return result


def _apply_transform(square, transform):
    reflected, quarter_turns = transform
    result = _flip_left_right(square) if reflected else [row[:] for row in square]
    for _ in range(quarter_turns):
        result = _rotate_ccw(result)
    return result


def solve(grid):
    # The visible layout is one header row over three n-by-n panels, with
    # one-column separators between the panels.
    n = len(grid) - 1
    if n <= 0 or any(len(row) < 3 * n + 2 for row in grid):
        return []

    marker = next((value for value in grid[0] if value != 0), 0)
    first = [row[0:n] for row in grid[1 : n + 1]]
    second = [row[n + 1 : 2 * n + 1] for row in grid[1 : n + 1]]
    third = [row[2 * n + 2 : 3 * n + 2] for row in grid[1 : n + 1]]

    matching = [
        transform
        for transform, transformed in _dihedral_transforms(first)
        if transformed == second
    ]
    if not matching:
        return [[0 for _ in range(n)] for _ in range(n)]

    # The examples make the mapping identifiable.  If the demonstration panel
    # has an accidental symmetry, prefer the first canonical representation.
    transformed_third = _apply_transform(third, matching[0])
    return [
        [marker if value != 0 else 0 for value in row]
        for row in transformed_third
    ]
