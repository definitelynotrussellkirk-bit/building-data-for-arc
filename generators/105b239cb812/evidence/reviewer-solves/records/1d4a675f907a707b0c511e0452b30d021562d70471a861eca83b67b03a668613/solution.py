from __future__ import annotations


def _copy(grid):
    return [list(row) for row in grid]


def _cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _rot180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _left_right(grid):
    return [list(reversed(row)) for row in grid]


def _up_down(grid):
    return [list(row) for row in reversed(grid)]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _anti_transpose(grid):
    return _rot180(_transpose(grid))


_TRANSFORMS = (
    ("cw", _cw),
    ("180", _rot180),
    ("ccw", _ccw),
    ("left_right", _left_right),
    ("up_down", _up_down),
    ("transpose", _transpose),
    ("anti_transpose", _anti_transpose),
    ("identity", _copy),
)


def solve(grid):
    """Infer the A->B square transform and apply it to square C."""
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) for row in grid):
        raise ValueError("expected a nonempty rectangular list grid")
    n = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid) or width != 3 * n + 2:
        raise ValueError("expected n x (3n+2) input")

    first_sep = n
    second_sep = 2 * n + 1
    if any(row[first_sep] != 5 or row[second_sep] != 5 for row in grid):
        raise ValueError("expected two full color-5 separator columns")

    panel_a = [row[:n] for row in grid]
    panel_b = [row[n + 1:2 * n + 1] for row in grid]
    panel_c = [row[2 * n + 2:] for row in grid]

    matches = [(name, transform) for name, transform in _TRANSFORMS if transform(panel_a) == panel_b]
    if len(matches) != 1:
        raise ValueError(f"expected one square transform mapping panel A to B, got {[name for name, _ in matches]}")
    return matches[0][1](panel_c)
