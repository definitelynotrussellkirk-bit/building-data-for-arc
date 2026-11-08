"""Visible-only solution for the blind reviewer episode."""


def solve(grid):
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two nonzero markers, got {len(points)}")

    (r1, c1), (r2, c2) = points
    row_sum = r1 + r2
    col_sum = c1 + c2
    if row_sum % 2 or col_sum % 2:
        raise ValueError("marker midpoint is not an integer grid cell")

    output = [[0 for _ in row] for row in grid]
    output[row_sum // 2][col_sum // 2] = 8
    return output
