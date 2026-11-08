from typing import Sequence


def _rotate_clockwise(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*reversed(grid))]


def solve(grid):
    """Arrange the input and its three rotations in a 2x2 pinwheel."""
    original = [list(row) for row in grid]
    clockwise = _rotate_clockwise(original)
    half_turn = _rotate_clockwise(clockwise)
    counterclockwise = _rotate_clockwise(half_turn)

    top = [left + right for left, right in zip(original, counterclockwise)]
    bottom = [left + right for left, right in zip(half_turn, clockwise)]
    return top + bottom
