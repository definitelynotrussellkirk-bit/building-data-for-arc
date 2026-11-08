"""Visible-only solution for blind task 23220e3be06f."""


def solve(grid):
    """Crop the lower figure and reflect it according to the corner marker.

    The isolated value at (0, 0) is an instruction rather than part of the
    figure: 5 requests a left/right reflection and 6 requests an up/down
    reflection.
    """
    marker = grid[0][0]
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    ]
    if not cells:
        return []

    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    cropped = [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]

    if marker == 5:
        return [row[::-1] for row in cropped]
    if marker == 6:
        return cropped[::-1]
    raise ValueError(f"unsupported reflection marker: {marker}")
