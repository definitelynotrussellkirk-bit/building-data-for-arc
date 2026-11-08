"""Visible-example solution for 17de34436a9f."""
from __future__ import annotations


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1], strict=True)]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the non-marker body and rotate it according to the 9-corner."""
    height = len(grid)
    width = len(grid[0])
    marker = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )
    body = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    min_r = min(r for r, _ in body)
    max_r = max(r for r, _ in body)
    min_c = min(c for _, c in body)
    max_c = max(c for _, c in body)
    cropped = [
        [0 if grid[r][c] == 9 else grid[r][c] for c in range(min_c, max_c + 1)]
        for r in range(min_r, max_r + 1)
    ]

    turns = {
        (0, 0): 0,
        (0, width - 1): 1,
        (height - 1, width - 1): 2,
        (height - 1, 0): 3,
    }[marker]
    for _ in range(turns):
        cropped = _rotate_clockwise(cropped)
    return cropped
