"""Visible-example solution for the reviewer-authored ARC episode."""


def solve(grid):
    """Rebuild the centered track and compress gray cells into a line.

    The two completely black parallel dividers reveal the track direction.
    The output keeps the same square size, moves those dividers to one cell
    either side of center, keeps the perpendicular center crossbar, and turns
    all gray cells into a centered one-cell-wide line along the track.
    """
    height = len(grid)
    width = len(grid[0])
    center_row = height // 2
    center_col = width // 2
    gray_count = sum(cell == 5 for row in grid for cell in row)

    full_black_rows = [r for r, row in enumerate(grid) if all(cell == 0 for cell in row)]
    full_black_cols = [
        c for c in range(width) if all(grid[r][c] == 0 for r in range(height))
    ]

    out = [[7 for _ in range(width)] for _ in range(height)]

    if len(full_black_rows) >= 2 and len(full_black_cols) < 2:
        # Horizontal track: parallel walls are rows; gray line runs horizontally.
        for c in range(width):
            out[center_row - 1][c] = 0
            out[center_row + 1][c] = 0
        for r in range(height):
            out[r][center_col] = 0
        start = center_col - gray_count // 2
        for c in range(start, start + gray_count):
            out[center_row][c] = 5
    elif len(full_black_cols) >= 2 and len(full_black_rows) < 2:
        # Vertical track: parallel walls are columns; gray line runs vertically.
        for r in range(height):
            out[r][center_col - 1] = 0
            out[r][center_col + 1] = 0
        for c in range(width):
            out[center_row][c] = 0
        start = center_row - gray_count // 2
        for r in range(start, start + gray_count):
            out[r][center_col] = 5
    else:
        raise ValueError("could not determine a unique track orientation")

    return out
