from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand every nonzero seed into a same-color cardinal plus."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    seeds = [
        (row, column, color)
        for row, values in enumerate(grid)
        for column, color in enumerate(values)
        if color != 0
    ]
    for row, column, color in seeds:
        for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = row + dr, column + dc
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = color
    return output
