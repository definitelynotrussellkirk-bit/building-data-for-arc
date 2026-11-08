"""Visible-example solution for the three-panel transform analogy."""


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rot270(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return [row[:] for row in grid[::-1]]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


_TRANSFORMS = (
    ("identity", lambda grid: [row[:] for row in grid]),
    ("rotate clockwise", _rot90),
    ("rotate 180", _rot180),
    ("rotate counterclockwise", _rot270),
    ("reflect left-right", _flip_lr),
    ("reflect top-bottom", _flip_ud),
    ("transpose", _transpose),
)


def _split_three_panels(grid):
    height = len(grid)
    divider_columns = [
        column
        for column in range(len(grid[0]))
        if all(grid[row][column] == 9 for row in range(height))
    ]
    if len(divider_columns) != 2:
        raise ValueError("expected exactly two full color-9 divider columns")
    left, right = divider_columns
    return (
        [row[:left] for row in grid],
        [row[left + 1:right] for row in grid],
        [row[right + 1:] for row in grid],
    )


def solve(grid):
    first, second, query = _split_three_panels(grid)
    matches = [operation for _, operation in _TRANSFORMS if operation(first) == second]
    if len(matches) != 1:
        raise ValueError(f"expected one demonstrated transform, found {len(matches)}")
    return matches[0](query)
