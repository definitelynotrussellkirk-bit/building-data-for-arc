from __future__ import annotations


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the lower object and apply the D4 transform encoded at (0, 0)."""
    if not grid or not grid[0]:
        return []

    transform = grid[0][0]
    work = [row[:] for row in grid]
    work[0][0] = 0

    occupied = [
        (row, col)
        for row, values in enumerate(work)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        return []

    min_row = min(row for row, _ in occupied)
    max_row = max(row for row, _ in occupied)
    min_col = min(col for _, col in occupied)
    max_col = max(col for _, col in occupied)
    crop = [row[min_col : max_col + 1] for row in work[min_row : max_row + 1]]

    if transform == 1:  # identity
        return crop
    if transform == 2:  # rotate 90 degrees clockwise
        return _rotate_cw(crop)
    if transform == 3:  # rotate 180 degrees
        return _rotate_180(crop)
    if transform == 4:  # rotate 90 degrees counterclockwise
        return _rotate_ccw(crop)
    if transform == 5:  # reflect left/right
        return [row[::-1] for row in crop]
    if transform == 6:  # reflect top/bottom
        return crop[::-1]
    if transform == 7:  # reflect across the main diagonal
        return _transpose(crop)
    if transform == 8:  # reflect across the anti-diagonal
        return _transpose(_rotate_180(crop))

    return crop
