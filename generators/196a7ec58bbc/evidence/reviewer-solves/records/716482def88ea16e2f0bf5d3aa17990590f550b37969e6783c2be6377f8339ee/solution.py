"""Visible-example solution for the review solve episode."""


def _rot90_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rot90_counterclockwise(grid):
    return [list(row) for row in zip(*grid)][::-1]


def solve(grid):
    """Tile the square input with its four rotations in spatial order.

    Quadrants are original (top-left), 90° clockwise (top-right),
    90° counterclockwise (bottom-left), and 180° (bottom-right).
    """
    if not grid or any(len(row) != len(grid) for row in grid):
        raise ValueError("expected a non-empty square grid")

    clockwise = _rot90_clockwise(grid)
    half_turn = _rot180(grid)
    counterclockwise = _rot90_counterclockwise(grid)

    top = [left + right for left, right in zip(grid, clockwise)]
    bottom = [left + right for left, right in zip(counterclockwise, half_turn)]
    return top + bottom
