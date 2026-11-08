from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill zero cells immediately bracketed by 4s on either cardinal axis."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height = len(source)
    width = len(source[0]) if height else 0

    for row in range(height):
        for col in range(width):
            if source[row][col] != 0:
                continue
            horizontal = (
                0 < col < width - 1
                and source[row][col - 1] == 4
                and source[row][col + 1] == 4
            )
            vertical = (
                0 < row < height - 1
                and source[row - 1][col] == 4
                and source[row + 1][col] == 4
            )
            if horizontal or vertical:
                output[row][col] = 4
    return output
