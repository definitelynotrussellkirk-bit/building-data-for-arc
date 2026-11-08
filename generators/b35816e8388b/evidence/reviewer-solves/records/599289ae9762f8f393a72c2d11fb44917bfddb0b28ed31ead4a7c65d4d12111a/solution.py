from __future__ import annotations


def solve(grid):
    """Return a blank grid with color 8 at the midpoint of the two markers."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two nonzero endpoints, got {len(points)}")

    (row_a, col_a), (row_b, col_b) = points
    if (row_a + row_b) % 2 or (col_a + col_b) % 2:
        raise ValueError("the two endpoints do not have an integer midpoint")

    output = [[0 for _ in range(width)] for _ in range(height)]
    output[(row_a + row_b) // 2][(col_a + col_b) // 2] = 8
    return output
