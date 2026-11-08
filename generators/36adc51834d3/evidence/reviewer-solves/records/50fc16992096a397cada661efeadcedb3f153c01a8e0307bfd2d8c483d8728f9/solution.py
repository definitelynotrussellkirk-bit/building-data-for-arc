from __future__ import annotations


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_counterclockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def solve(grid):
    """Remove the corner command, crop the object, and apply its quarter-turn."""
    if not grid or not grid[0]:
        return []

    command = int(grid[0][0])
    cleaned = [list(row) for row in grid]
    cleaned[0][0] = 0

    occupied = [
        (row, col)
        for row, values in enumerate(cleaned)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        return []

    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    crop = [values[left : right + 1] for values in cleaned[top : bottom + 1]]

    if command == 1:
        return crop
    if command == 2:
        return _rotate_clockwise(crop)
    if command == 3:
        return _rotate_180(crop)
    if command == 4:
        return _rotate_counterclockwise(crop)
    raise ValueError(f"unsupported command {command!r}")
