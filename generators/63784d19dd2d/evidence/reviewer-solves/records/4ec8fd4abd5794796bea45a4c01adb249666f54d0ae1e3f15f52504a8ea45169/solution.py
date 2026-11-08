"""Visible-example solution for blind task 63784d19dd2d.

The input contains three square panels separated by two one-column dividers.
The first two panels demonstrate a symmetry of the whole square; the answer is
obtained by applying the same symmetry to the third panel.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

Grid = list[list[int]]
CoordTransform = Callable[[int, int, int], tuple[int, int]]


def _identity(r: int, c: int, n: int) -> tuple[int, int]:
    return r, c


def _rotate_90_clockwise(r: int, c: int, n: int) -> tuple[int, int]:
    return c, n - 1 - r


def _rotate_180(r: int, c: int, n: int) -> tuple[int, int]:
    return n - 1 - r, n - 1 - c


def _rotate_270_clockwise(r: int, c: int, n: int) -> tuple[int, int]:
    return n - 1 - c, r


def _reflect_left_right(r: int, c: int, n: int) -> tuple[int, int]:
    return r, n - 1 - c


def _reflect_top_bottom(r: int, c: int, n: int) -> tuple[int, int]:
    return n - 1 - r, c


def _reflect_main_diagonal(r: int, c: int, n: int) -> tuple[int, int]:
    return c, r


def _reflect_anti_diagonal(r: int, c: int, n: int) -> tuple[int, int]:
    return n - 1 - c, n - 1 - r


_TRANSFORMS: tuple[CoordTransform, ...] = (
    _identity,
    _rotate_90_clockwise,
    _rotate_180,
    _rotate_270_clockwise,
    _reflect_left_right,
    _reflect_top_bottom,
    _reflect_main_diagonal,
    _reflect_anti_diagonal,
)


def _apply(panel: Sequence[Sequence[int]], transform: CoordTransform) -> Grid:
    n = len(panel)
    if n == 0 or any(len(row) != n for row in panel):
        raise ValueError("each panel must be a non-empty square")

    result = [[0 for _ in range(n)] for _ in range(n)]
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            rr, cc = transform(r, c, n)
            result[rr][cc] = value
    return result


def _occupancy(panel: Sequence[Sequence[int]]) -> Grid:
    return [[int(value != 0) for value in row] for row in panel]


def _split_panels(grid: Sequence[Sequence[int]]) -> tuple[Grid, Grid, Grid]:
    n = len(grid)
    if n == 0 or any(len(row) != 3 * n + 2 for row in grid):
        raise ValueError("expected three n×n panels separated by two columns")

    first = [list(row[:n]) for row in grid]
    second = [list(row[n + 1 : 2 * n + 1]) for row in grid]
    third = [list(row[2 * n + 2 :]) for row in grid]
    return first, second, third


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Apply the demonstrated square symmetry to the third panel."""

    first, second, third = _split_panels(grid)
    first_mask = _occupancy(first)
    second_mask = _occupancy(second)

    matches = [
        transform
        for transform in _TRANSFORMS
        if _apply(first_mask, transform) == second_mask
    ]
    if not matches:
        raise ValueError("the first two panels do not define a square symmetry")

    # A symmetric teaching shape can admit more than one named symmetry. Accept
    # that only when all matching symmetries make the same prediction.
    predictions = [_apply(third, transform) for transform in matches]
    if any(prediction != predictions[0] for prediction in predictions[1:]):
        raise ValueError("the demonstrated symmetry is ambiguous for the query panel")
    return predictions[0]
