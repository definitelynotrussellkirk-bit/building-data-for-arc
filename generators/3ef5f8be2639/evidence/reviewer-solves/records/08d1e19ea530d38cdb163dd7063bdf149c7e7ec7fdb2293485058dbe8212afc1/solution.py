"""Visible-example solution for ARC task 3ef5f8be2639."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0]) if height else 0

    def first(color: int) -> tuple[int, int]:
        for row, values in enumerate(grid):
            for col, value in enumerate(values):
                if value == color:
                    return row, col
        raise ValueError(f"input has no color-{color} seed")

    def grown(center: tuple[int, int]) -> set[tuple[int, int]]:
        row, col = center
        return {
            (r, c)
            for r in range(row - 1, row + 2)
            for c in range(col - 1, col + 2)
            if 0 <= r < height and 0 <= c < width
        }

    overlap = grown(first(2)) & grown(first(3))
    return [
        [8 if (row, col) in overlap else 0 for col in range(width)]
        for row in range(height)
    ]
