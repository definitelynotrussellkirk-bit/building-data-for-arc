"""Solve the framed A:B::C transform-transfer puzzle from visible examples."""


def _identity(grid):
    return [row[:] for row in grid]


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rot270(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return [row[:] for row in grid[::-1]]


def _anti_transpose(grid):
    return [list(row) for row in zip(*grid[::-1])][::-1]


_TRANSFORMS = (
    _identity,
    _rot90,
    _rot180,
    _rot270,
    _transpose,
    _flip_lr,
    _flip_ud,
    _anti_transpose,
)


def _panel(grid, start_col):
    return [row[start_col : start_col + 4] for row in grid[1:5]]


def solve(grid):
    """Infer the square symmetry mapping A to B and apply it to C."""
    a = _panel(grid, 1)
    b = _panel(grid, 8)
    c = _panel(grid, 15)
    matches = [transform for transform in _TRANSFORMS if transform(a) == b]
    if not matches:
        raise ValueError("no supported transform maps panel A to panel B")
    return matches[0](c)
