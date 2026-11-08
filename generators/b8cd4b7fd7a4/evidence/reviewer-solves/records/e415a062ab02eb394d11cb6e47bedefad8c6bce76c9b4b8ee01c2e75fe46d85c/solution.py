"""Visible-example solution for the prepared b8cd4b7fd7a4 episode."""


def _sign(value):
    return (value > 0) - (value < 0)


def solve(grid):
    """Paint cyan only on the strict lattice segment between two markers."""
    height = len(grid)
    width = len(grid[0])
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(points) != 2:
        raise ValueError(f"expected two nonzero markers, found {len(points)}")

    (row1, col1), (row2, col2) = points
    delta_row = row2 - row1
    delta_col = col2 - col1
    if not (
        (delta_row == 0 and delta_col != 0)
        or (delta_col == 0 and delta_row != 0)
        or (delta_row != 0 and abs(delta_row) == abs(delta_col))
    ):
        raise ValueError("markers are not horizontally, vertically, or diagonally aligned")

    distance = max(abs(delta_row), abs(delta_col))
    step_row = _sign(delta_row)
    step_col = _sign(delta_col)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for offset in range(1, distance):
        output[row1 + offset * step_row][col1 + offset * step_col] = 8
    return output
