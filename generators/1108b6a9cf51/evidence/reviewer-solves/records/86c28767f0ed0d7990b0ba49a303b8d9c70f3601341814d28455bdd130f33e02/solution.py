from __future__ import annotations

from typing import Callable, Sequence

Grid = list[list[int]]


def _rotate_clockwise(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_counterclockwise(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_horizontal(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(reversed(row)) for row in grid]


def _flip_vertical(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in reversed(grid)]


def _transpose(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in zip(*grid)]


def _anti_transpose(grid: Sequence[Sequence[int]]) -> Grid:
    # Reflection across the anti-diagonal.
    return _flip_horizontal(_rotate_counterclockwise(grid))


def _identity(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


_TRANSFORMS: tuple[Callable[[Sequence[Sequence[int]]], Grid], ...] = (
    _identity,
    _rotate_clockwise,
    _rotate_180,
    _rotate_counterclockwise,
    _flip_horizontal,
    _flip_vertical,
    _transpose,
    _anti_transpose,
)


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Infer the square symmetry mapping panel 1 to panel 2 and apply it to panel 3."""
    height = len(grid)
    if height == 0 or any(len(row) != 3 * height + 2 for row in grid):
        raise ValueError("expected three HxH panels separated by one-column dividers")

    first = [list(row[:height]) for row in grid]
    second = [list(row[height + 1 : 2 * height + 1]) for row in grid]
    third = [list(row[2 * height + 2 :]) for row in grid]

    matches = [transform for transform in _TRANSFORMS if transform(first) == second]
    if not matches:
        raise ValueError("no square symmetry maps the first panel to the second")

    # A symmetric first panel can admit duplicate mappings. Generated lessons are
    # expected to make their action on the third panel unambiguous.
    outputs = [transform(third) for transform in matches]
    if any(output != outputs[0] for output in outputs[1:]):
        raise ValueError("visible relation is ambiguous on the third panel")
    return outputs[0]
